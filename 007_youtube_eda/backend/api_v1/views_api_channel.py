import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.db.models import Sum

from .models import Channel, CollectionLog, VideoStats


def _view_sum(channel) -> int:
    """채널에 수집된 영상의 조회수 합계 (VideoStats 기준)"""
    result = (
        VideoStats.objects
        .filter(video__channel=channel)
        .aggregate(total=Sum('view_count'))
    )
    return result['total'] or 0


# ── 채널 목록 ─────────────────────────────────────────────────────────────────

@require_GET
def channel_list(request):
    """수집된 전체 채널 목록 + 최근 수집 로그"""

    sort    = request.GET.get('sort', 'fetched_at')
    keyword = request.GET.get('q', '').strip()

    qs = Channel.objects.all()
    if keyword:
        qs = qs.filter(channel_name__icontains=keyword)

    if sort == 'subscriber':
        qs = qs.order_by('-subscriber_count')
    elif sort == 'video':
        qs = qs.order_by('-video_count')
    else:
        qs = qs.order_by('-fetched_at')

    channels     = []
    total_videos = 0
    total_views  = 0

    for ch in qs:
        latest = (
            CollectionLog.objects
            .filter(channel=ch)
            .order_by('-started_at')
            .first()
        )
        video_cnt  = ch.videos.count()
        view_count = _view_sum(ch)          # ← VideoStats 합산

        total_videos += video_cnt
        total_views  += view_count

        channels.append({
            'channel_id':       ch.channel_id,
            'channel_name':     ch.channel_name,
            'channel_url':      ch.channel_url,
            'subscriber_count': ch.subscriber_count,
            'video_count':      video_cnt,
            'total_view_count': view_count,  # ← 실제 합산값
            'thumbnail_url':    ch.thumbnail_url or '',
            'banner_url':       ch.banner_url or '',
            'country':          ch.country or '',
            'description':      (ch.description or '')[:200],
            'created_at':       ch.created_at.strftime('%Y-%m-%d %H:%M') if ch.created_at else '',
            'fetched_at':       ch.fetched_at.strftime('%Y-%m-%d %H:%M') if ch.fetched_at else '',
            'log': {
                'id':               latest.id,
                'status':           latest.status,
                'total_videos':     latest.total_videos,
                'collected_videos': latest.collected_videos,
                'started_at':       latest.started_at.strftime('%Y-%m-%d %H:%M') if latest.started_at else '',
                'finished_at':      latest.finished_at.strftime('%Y-%m-%d %H:%M') if latest.finished_at else '',
            } if latest else None,
        })

    return JsonResponse({
        'success':      True,
        'total':        len(channels),
        'total_videos': total_videos,
        'total_views':  total_views,
        'channels':     channels,
    })


# ── 채널 상세 ─────────────────────────────────────────────────────────────────

@require_GET
def channel_detail(request, channel_id):
    """채널 상세 정보 + 최근 수집 로그 5건"""
    try:
        ch = Channel.objects.get(channel_id=channel_id)
    except Channel.DoesNotExist:
        return JsonResponse({'error': '채널을 찾을 수 없습니다.'}, status=404)

    logs = CollectionLog.objects.filter(channel=ch).order_by('-started_at')[:5]

    return JsonResponse({
        'success': True,
        'channel': {
            'channel_id':       ch.channel_id,
            'channel_name':     ch.channel_name,
            'channel_url':      ch.channel_url,
            'subscriber_count': ch.subscriber_count,
            'video_count':      ch.videos.count(),
            'total_view_count': _view_sum(ch),   # ← 실제 합산값
            'thumbnail_url':    ch.thumbnail_url or '',
            'country':          ch.country or '',
            'description':      ch.description or '',
            'created_at':       ch.created_at.strftime('%Y-%m-%d %H:%M') if ch.created_at else '',
            'fetched_at':       ch.fetched_at.strftime('%Y-%m-%d %H:%M') if ch.fetched_at else '',
        },
        'logs': [
            {
                'id':               lg.id,
                'status':           lg.status,
                'total_videos':     lg.total_videos,
                'collected_videos': lg.collected_videos,
                'error_message':    lg.error_message or '',
                'started_at':       lg.started_at.strftime('%Y-%m-%d %H:%M') if lg.started_at else '',
                'finished_at':      lg.finished_at.strftime('%Y-%m-%d %H:%M') if lg.finished_at else '',
            }
            for lg in logs
        ],
    })


# ── 수집 로그 목록 ────────────────────────────────────────────────────────────

@require_GET
def collection_logs(request):
    """채널별 수집 로그 목록 (최신순)"""
    channel_id = request.GET.get('channel_id', 'all')
    limit      = min(int(request.GET.get('limit', 30)), 100)

    qs = CollectionLog.objects.select_related('channel').order_by('-started_at')
    if channel_id != 'all':
        qs = qs.filter(channel__channel_id=channel_id)

    result = []
    for lg in qs[:limit]:
        pct = round((lg.collected_videos / lg.total_videos) * 100) if lg.total_videos else 0
        result.append({
            'id':               lg.id,
            'channel_id':       lg.channel.channel_id,
            'channel_name':     lg.channel.channel_name,
            'status':           lg.status,
            'total_videos':     lg.total_videos,
            'collected_videos': lg.collected_videos,
            'percent':          pct,
            'error_message':    lg.error_message or '',
            'started_at':       lg.started_at.strftime('%Y-%m-%d %H:%M') if lg.started_at else '',
            'finished_at':      lg.finished_at.strftime('%Y-%m-%d %H:%M') if lg.finished_at else '',
        })

    return JsonResponse({'success': True, 'total': len(result), 'logs': result})


# ── 채널 삭제 ─────────────────────────────────────────────────────────────────

@csrf_exempt
def channel_delete(request, channel_id):
    """채널 + 연관 영상/로그 삭제 (CASCADE)"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE만 허용됩니다.'}, status=405)
    try:
        ch = Channel.objects.get(channel_id=channel_id)
        name = ch.channel_name
        ch.delete()
        return JsonResponse({'success': True, 'message': f'"{name}" 채널이 삭제되었습니다.'})
    except Channel.DoesNotExist:
        return JsonResponse({'error': '채널을 찾을 수 없습니다.'}, status=404)
