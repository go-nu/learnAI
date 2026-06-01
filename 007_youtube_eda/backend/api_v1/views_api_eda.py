from collections import defaultdict
from datetime import date

from django.db.models import Sum, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Channel, Video, VideoStats


def _fmt(secs: int) -> str:
    secs = int(secs or 0)
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


@require_GET
def eda_data(request):
    channel_id = request.GET.get('channel_id', 'all')

    # ── 채널 / 영상 쿼리셋 필터 ───────────────────────────────────────────────
    if channel_id == 'all':
        channels = Channel.objects.all()
        videos   = Video.objects.all()
    else:
        channels = Channel.objects.filter(channel_id=channel_id)
        videos   = Video.objects.filter(channel__channel_id=channel_id)

    total_videos = videos.count()

    # ── KPI ─────────────────────────────────────────────────────────────────
    total_views = (
        VideoStats.objects.filter(video__in=videos)
        .aggregate(s=Sum('view_count'))['s'] or 0
    )
    avg_views = total_views // total_videos if total_videos else 0

    # ── 월별 업로드 추이 (최근 12개월) ──────────────────────────────────────
    today = date.today()
    month_list = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12; y -= 1
        month_list.append((y, m))

    monthly = defaultdict(int)
    for v in videos.values('published_at'):
        if v['published_at']:
            monthly[(v['published_at'].year, v['published_at'].month)] += 1

    upload_trend = {
        'labels': [f'{str(y)[-2:]}.{m:02d}' for y, m in month_list],
        'data':   [monthly.get(ym, 0) for ym in month_list],
    }

    # ── 조회수 분포 ──────────────────────────────────────────────────────────
    vc_list = list(
        VideoStats.objects.filter(video__in=videos)
        .values_list('view_count', flat=True)
    )
    dist = [0] * 6
    for v in vc_list:
        v = v or 0
        if   v < 10_000:      dist[0] += 1
        elif v < 50_000:      dist[1] += 1
        elif v < 100_000:     dist[2] += 1
        elif v < 500_000:     dist[3] += 1
        elif v < 1_000_000:   dist[4] += 1
        else:                 dist[5] += 1

    # ── Shorts / 일반 비율 ───────────────────────────────────────────────────
    shorts_cnt  = videos.filter(is_short=True).count()
    regular_cnt = total_videos - shorts_cnt

    # ── 요일별 업로드 ────────────────────────────────────────────────────────
    weekday = [0] * 7
    for v in videos.values('published_at'):
        if v['published_at']:
            weekday[v['published_at'].weekday()] += 1

    # ── 산점도: 영상 길이 vs 조회수 (최대 150개) ─────────────────────────────
    scatter_r, scatter_s = [], []
    qs = (
        videos.select_related('stats')
        .filter(duration_seconds__gt=0)
        .order_by('-stats__view_count')[:150]
    )
    for v in qs:
        try:
            pt = {'x': v.duration_seconds, 'y': v.stats.view_count or 0}
            (scatter_s if v.is_short else scatter_r).append(pt)
        except Exception:
            pass

    # ── TOP 10 영상 ──────────────────────────────────────────────────────────
    top10 = []
    for i, st in enumerate(
        VideoStats.objects.filter(video__in=videos)
        .select_related('video', 'video__channel')
        .order_by('-view_count')[:10]
    ):
        v = st.video
        top10.append({
            'rank':     i + 1,
            'title':    v.title,
            'channel':  v.channel.channel_name,
            'views':    st.view_count or 0,
            'likes':    st.like_count or 0,
            'comments': st.comment_count or 0,
            'duration': _fmt(v.duration_seconds),
            'is_short': v.is_short,
        })

    # ── 채널별 참여도 ────────────────────────────────────────────────────────
    engagement = []
    for ch in list(channels)[:8]:
        agg = (
            VideoStats.objects.filter(video__channel=ch)
            .aggregate(al=Avg('like_count'), ac=Avg('comment_count'))
        )
        engagement.append({
            'channel':      ch.channel_name,
            'avg_likes':    round(agg['al'] or 0),
            'avg_comments': round(agg['ac'] or 0),
        })

    # ── 참여도 지표 요약 ─────────────────────────────────────────────────────
    engagement_agg = (
        VideoStats.objects.filter(video__in=videos)
        .aggregate(al=Avg('like_count'), ac=Avg('comment_count'), av=Avg('view_count'))
    )
    avg_likes    = round(engagement_agg['al'] or 0)
    avg_comments = round(engagement_agg['ac'] or 0)
    avg_view_for_rate = engagement_agg['av'] or 1
    like_rate    = round(avg_likes / avg_view_for_rate * 100, 2) if avg_view_for_rate else 0

    return JsonResponse({
        'success':    True,
        'channel_id': channel_id,
        'kpi': {
            'channel_count': channels.count(),
            'total_videos':  total_videos,
            'total_views':   total_views,
            'avg_views':     avg_views,
        },
        'upload_trend': upload_trend,
        'views_dist': {
            'labels': ['~1만', '1~5만', '5~10만', '10~50만', '50~100만', '100만+'],
            'data':   dist,
        },
        'shorts_ratio': {'regular': regular_cnt, 'shorts': shorts_cnt},
        'weekday': {
            'labels': ['월', '화', '수', '목', '금', '토', '일'],
            'data':   weekday,
        },
        'scatter': {'regular': scatter_r, 'shorts': scatter_s},
        'top10':   top10,
        'engagement':       engagement,
        'engagement_summary': {
            'avg_likes':    avg_likes,
            'avg_comments': avg_comments,
            'like_rate':    like_rate,
        },
    })
