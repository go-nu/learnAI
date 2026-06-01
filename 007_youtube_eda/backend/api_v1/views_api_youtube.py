import json
import threading
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection as db_conn

try:
    import yt_dlp
    YT_DLP_OK = True
except ImportError:
    YT_DLP_OK = False

from .models import Channel, Video, VideoStats, Tag, VideoTag, CollectionLog

# 메모리 진행 상태 (log_id → dict)
_progress: dict[int, dict] = {}


def _set(log_id: int, **kw):
    _progress.setdefault(log_id, {}).update(kw)


def _pick_banner(thumbnails: list) -> str:
    """yt-dlp thumbnails 중 배너 이미지 선택.
    YouTube 배너는 가로가 매우 넓은 이미지(가로/세로 비율 > 2.5)로 식별."""
    if not thumbnails:
        return ''
    candidates = [
        t for t in thumbnails
        if isinstance(t, dict)
        and int(t.get('width') or 0) >= 480
        and int(t.get('height') or 1) > 0
        and (int(t.get('width') or 0) / int(t.get('height') or 1)) >= 2.5
    ]
    if candidates:
        best = max(candidates, key=lambda t: int(t.get('width') or 0))
        return best.get('url', '')
    return ''


# ── 채널 정보 수집 ─────────────────────────────────────────────────────────────

@csrf_exempt
def fetch_channel(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST만 허용됩니다.'}, status=405)
    if not YT_DLP_OK:
        return JsonResponse({'error': 'yt-dlp 미설치. pip install yt-dlp'}, status=500)

    try:
        body = json.loads(request.body)
        url  = body.get('url', '').strip()
        if not url:
            return JsonResponse({'error': 'URL을 입력해주세요.'}, status=400)

        opts = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'playlist_items': '1',
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        channel_id = (
            info.get('channel_id')
            or info.get('uploader_id')
            or info.get('id', '')
        )
        if not channel_id:
            return JsonResponse({'error': '채널 ID를 가져올 수 없습니다. URL을 확인해주세요.'}, status=400)

        channel_name     = info.get('channel') or info.get('uploader') or info.get('title', '알 수 없음')
        subscriber_count = info.get('channel_follower_count') or 0
        thumbnail        = info.get('thumbnail') or ''
        description      = (info.get('description') or '')[:2000]
        country          = info.get('country') or ''
        banner_url       = _pick_banner(info.get('thumbnails') or [])

        channel, _ = Channel.objects.update_or_create(
            channel_id=channel_id,
            defaults=dict(
                channel_url=url,
                channel_name=channel_name,
                subscriber_count=subscriber_count,
                thumbnail_url=thumbnail,
                banner_url=banner_url,
                description=description,
                country=country,
            ),
        )

        return JsonResponse({
            'success': True,
            'channel': {
                'channel_id':       channel.channel_id,
                'channel_name':     channel.channel_name,
                'channel_url':      channel.channel_url,
                'subscriber_count': channel.subscriber_count,
                'video_count':      channel.video_count,
                'thumbnail_url':    channel.thumbnail_url,
                'banner_url':       channel.banner_url,
                'description':      (channel.description or '')[:300],
                'country':          channel.country,
            },
        })

    except yt_dlp.utils.DownloadError as e:
        return JsonResponse({'error': f'채널을 찾을 수 없습니다: {e}'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'오류: {e}'}, status=500)


# ── 영상 수집 (백그라운드 스레드) ──────────────────────────────────────────────

MAX_VIDEOS = 50   # 최대 수집 영상 수 (일반 영상 / Shorts 각각)


def _fetch_ids(url: str, limit: int) -> list[str]:
    """yt-dlp로 플레이리스트/탭 URL에서 영상 ID 목록 수집"""
    opts = {'extract_flat': True, 'skip_download': True, 'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return [e.get('id') for e in (info.get('entries') or []) if e.get('id')][:limit]
    except Exception:
        return []


def _worker(channel_id: str, log_id: int,
            max_videos: int = MAX_VIDEOS, max_shorts: int = MAX_VIDEOS):
    """일반 영상 + Shorts 분리 수집 백그라운드 스레드"""
    try:
        channel = Channel.objects.get(channel_id=channel_id)
        log     = CollectionLog.objects.get(id=log_id)
        log.status = CollectionLog.STATUS_RUNNING
        log.save()

        # ── 1단계: 일반 영상 ID 수집 (/videos 탭) ───────────────────────────
        _set(log_id, status='running', current='📹 일반 영상 목록을 조회하고 있습니다...')
        video_ids = _fetch_ids(channel.channel_url + '/videos', max_videos) if max_videos > 0 else []
        _set(log_id, videos_found=len(video_ids),
             current=f'📹 일반 영상 {len(video_ids)}개 발견')

        # ── 2단계: Shorts ID 수집 (/shorts 탭) ──────────────────────────────
        _set(log_id, current='🩳 YouTube Shorts 목록을 조회하고 있습니다...')
        short_ids = _fetch_ids(channel.channel_url + '/shorts', max_shorts) if max_shorts > 0 else []
        _set(log_id, shorts_found=len(short_ids),
             current=f'🩳 Shorts {len(short_ids)}개 발견')

        # ── 3단계: 합치기 (중복 제거, video_ids 우선) ───────────────────────
        seen, all_ids = set(), []
        for vid in video_ids + short_ids:
            if vid not in seen:
                seen.add(vid); all_ids.append(vid)

        short_id_set = set(short_ids) - set(video_ids)   # 순수 Shorts (일반탭에 없는 것)

        log.total_videos = len(all_ids)
        log.save()
        _set(
            log_id, total=len(all_ids),
            current=(
                f'총 {len(all_ids)}개 수집 시작 '
                f'(일반 영상 {len(video_ids)}개 + Shorts {len(short_ids)}개)'
            ),
        )

        # ── 4단계: 영상 상세 정보 ───────────────────────────────────────────
        detail_opts = {'skip_download': True, 'quiet': True, 'no_warnings': True}

        for idx, vid in enumerate(all_ids):
            type_label = '🩳 Shorts' if vid in short_id_set else '📹 일반 영상'
            try:
                _set(log_id,
                     current=f'[{idx+1}/{len(all_ids)}] {type_label} 수집 중...',
                     current_type=type_label, collected=idx + 1)

                with yt_dlp.YoutubeDL(detail_opts) as ydl:
                    vi = ydl.extract_info(f'https://www.youtube.com/watch?v={vid}', download=False)

                title = vi.get('title', '')
                _set(log_id, current=f'[{idx+1}/{len(all_ids)}] {type_label} — {title}')

                pub = None
                if ud := vi.get('upload_date'):
                    pub = datetime.strptime(ud, '%Y%m%d').date()

                video, _ = Video.objects.update_or_create(
                    video_id=vid,
                    defaults=dict(
                        channel=channel,
                        title=title,
                        description=(vi.get('description') or '')[:3000],
                        published_at=pub,
                        duration_seconds=vi.get('duration') or 0,
                        thumbnail_url=vi.get('thumbnail') or '',
                    ),
                )
                VideoStats.objects.update_or_create(
                    video=video,
                    defaults=dict(
                        view_count=vi.get('view_count') or 0,
                        like_count=vi.get('like_count') or 0,
                        comment_count=vi.get('comment_count') or 0,
                    ),
                )
                for tag_name in (vi.get('tags') or [])[:10]:
                    if tag_name:
                        tag, _ = Tag.objects.get_or_create(name=tag_name[:100])
                        VideoTag.objects.get_or_create(video=video, tag=tag)

            except Exception:
                pass

            log.collected_videos = idx + 1
            log.save()

        channel.video_count = log.collected_videos
        channel.save()

        log.status      = CollectionLog.STATUS_DONE
        log.finished_at = datetime.now()
        log.save()
        _set(log_id, status='done', current='✅ 모든 영상 수집이 완료되었습니다!')

    except Exception as e:
        try:
            log = CollectionLog.objects.get(id=log_id)
            log.status        = CollectionLog.STATUS_ERROR
            log.error_message = str(e)[:1000]
            log.finished_at   = datetime.now()
            log.save()
        except Exception:
            pass
        _set(log_id, status='error', current=f'오류 발생: {e}')
    finally:
        db_conn.close()


@csrf_exempt
def fetch_videos(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST만 허용됩니다.'}, status=405)
    if not YT_DLP_OK:
        return JsonResponse({'error': 'yt-dlp 미설치.'}, status=500)

    try:
        body       = json.loads(request.body)
        channel_id = body.get('channel_id', '').strip()
        if not channel_id:
            return JsonResponse({'error': 'channel_id가 필요합니다.'}, status=400)

        # max_videos / max_shorts: 0~50 범위로 강제 클램프 (0 = 수집 안 함)
        max_videos = int(body.get('max_videos', MAX_VIDEOS))
        max_videos = max(0, min(max_videos, MAX_VIDEOS))
        max_shorts = int(body.get('max_shorts', MAX_VIDEOS))
        max_shorts = max(0, min(max_shorts, MAX_VIDEOS))
        if max_videos == 0 and max_shorts == 0:
            return JsonResponse({'error': '일반 영상 또는 Shorts 중 하나는 1개 이상 설정해주세요.'}, status=400)

        channel = Channel.objects.get(channel_id=channel_id)

        # 이미 실행 중인 작업 확인
        running = CollectionLog.objects.filter(
            channel=channel,
            status=CollectionLog.STATUS_RUNNING,
        ).first()
        if running:
            return JsonResponse({'success': True, 'log_id': running.id, 'already_running': True})

        log = CollectionLog.objects.create(
            channel=channel,
            status=CollectionLog.STATUS_PENDING,
        )
        threading.Thread(
            target=_worker,
            args=(channel_id, log.id, max_videos, max_shorts),
            daemon=True,
        ).start()

        return JsonResponse({
            'success':         True,
            'log_id':          log.id,
            'already_running': False,
            'max_videos':      max_videos,
            'max_shorts':      max_shorts,
        })

    except Channel.DoesNotExist:
        return JsonResponse({'error': '채널을 먼저 수집해주세요.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 요청 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ── 수집 상태 조회 ─────────────────────────────────────────────────────────────

def collection_status(request, log_id: int):
    try:
        log  = CollectionLog.objects.get(id=log_id)
        prog = _progress.get(log_id, {})
        pct  = round((log.collected_videos / log.total_videos) * 100) if log.total_videos else 0

        return JsonResponse({
            'success':          True,
            'status':           log.status,
            'total_videos':     log.total_videos,
            'collected_videos': log.collected_videos,
            'percent':          pct,
            'current':          prog.get('current', ''),
            'current_type':     prog.get('current_type', ''),
            'videos_found':     prog.get('videos_found', 0),
            'shorts_found':     prog.get('shorts_found', 0),
            'error_message':    log.error_message,
            'started_at':       log.started_at.strftime('%Y-%m-%d %H:%M:%S') if log.started_at else None,
            'finished_at':      log.finished_at.strftime('%Y-%m-%d %H:%M:%S') if log.finished_at else None,
        })
    except CollectionLog.DoesNotExist:
        return JsonResponse({'error': '수집 로그를 찾을 수 없습니다.'}, status=404)
