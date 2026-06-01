import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Channel, AiAnalysisReport


@csrf_exempt
@require_POST
def save_ai_report(request):
    """Gemini가 생성한 AI 분석 결과를 DB에 저장"""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': '잘못된 JSON 형식입니다.'}, status=400)

    channel_id = body.get('channel_id', '').strip()
    summary    = body.get('summary', '')
    insights   = body.get('insights', [])

    if not channel_id or channel_id == 'all':
        return JsonResponse({'success': False, 'error': '유효한 channel_id가 필요합니다.'}, status=400)

    try:
        channel = Channel.objects.get(pk=channel_id)
    except Channel.DoesNotExist:
        return JsonResponse({'success': False, 'error': '채널을 찾을 수 없습니다.'}, status=404)

    report = AiAnalysisReport.objects.create(
        channel=channel,
        summary=summary,
        insights=insights,
    )
    return JsonResponse({
        'success': True,
        'report_id': report.id,
        'created_at': report.created_at.strftime('%Y-%m-%d %H:%M'),
    })


@require_GET
def get_latest_ai_report(request):
    """채널의 가장 최근 AI 분석 리포트 반환"""
    channel_id = request.GET.get('channel_id', '').strip()

    if not channel_id or channel_id == 'all':
        return JsonResponse({'success': True, 'report': None})

    report = AiAnalysisReport.objects.filter(channel_id=channel_id).first()
    if not report:
        return JsonResponse({'success': True, 'report': None})

    return JsonResponse({
        'success': True,
        'report': {
            'id': report.id,
            'summary': report.summary,
            'insights': report.insights,
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M'),
        },
    })
