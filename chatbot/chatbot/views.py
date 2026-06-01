import json
import os
import shutil
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from .models import LoginLog, RagConfig, ChatSession, ChatMessage


def _get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def _is_admin(user):
    return user.is_staff or user.is_superuser


@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        if _is_admin(request.user):
            return redirect('dashboard')
        return redirect('chatbot')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'}, status=400)

        email    = data.get('email', '').strip()
        password = data.get('password', '')

        if not email or not password:
            return JsonResponse({'success': False, 'error': '이메일과 비밀번호를 입력해 주세요.'}, status=400)

        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        except User.MultipleObjectsReturned:
            return JsonResponse({'success': False, 'error': '중복 계정이 존재합니다. 관리자에게 문의하세요.'}, status=400)

        if user is not None and user.is_active:
            login(request, user)
            if _is_admin(user):
                return JsonResponse({'success': True, 'redirect': '/chatbot/dashboard/'})
            return JsonResponse({'success': True, 'redirect': '/chatbot/chat/'})

        # 로그인 실패 기록
        fail_username = ''
        try:
            fail_user = User.objects.get(email=email)
            fail_username = fail_user.username
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            fail_username = email
        LoginLog.objects.create(
            user=None,
            username=fail_username,
            email=email,
            action=LoginLog.ACTION_FAIL,
            client_ip=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
            is_admin=False,
        )
        return JsonResponse({'success': False, 'error': '이메일 또는 비밀번호가 올바르지 않습니다.'}, status=401)

    return render(request, 'dashboard/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/chatbot/login/')
def dashboard(request):
    if not _is_admin(request.user):
        return redirect('chatbot')
    return render(request, 'dashboard/dashboard.html', {'active_nav': 'overview'})


@login_required(login_url='/chatbot/login/')
def dashboard_rags(request):
    rags = RagConfig.objects.filter(is_active=True).order_by('-created_at')
    data = [{
        'id': r.id,
        'name': r.name,
        'status': r.status,
        'llm_model': r.llm_model,
        'chunk_count': r.chunk_count,
        'created_at': r.created_at.strftime('%Y-%m-%d'),
    } for r in rags]
    return JsonResponse({'rags': data})


@login_required(login_url='/chatbot/login/')
def dashboard_stats(request):
    import datetime
    from zoneinfo import ZoneInfo
    from django.utils import timezone
    from django.db.models import Avg, Count, Sum

    SEOUL = ZoneInfo('Asia/Seoul')
    now          = timezone.now()
    now_seoul    = now.astimezone(SEOUL)
    today_seoul  = now_seoul.date()
    active_cutoff = now - datetime.timedelta(minutes=30)

    # 오늘(서울) 자정 UTC 범위로 필터 (CONVERT_TZ 없이)
    today_start_utc = datetime.datetime.combine(today_seoul, datetime.time.min, tzinfo=SEOUL).astimezone(datetime.timezone.utc)
    today_end_utc   = datetime.datetime.combine(today_seoul, datetime.time.max, tzinfo=SEOUL).astimezone(datetime.timezone.utc)
    today_messages  = ChatMessage.objects.filter(created_at__gte=today_start_utc, created_at__lte=today_end_utc).count()
    active_sessions = ChatSession.objects.filter(updated_at__gte=active_cutoff).count()
    ready_rags      = RagConfig.objects.filter(status='ready', is_active=True).count()
    total_chunks    = RagConfig.objects.filter(status='ready', is_active=True).aggregate(
                          t=Sum('chunk_count'))['t'] or 0
    avg_ms          = ChatMessage.objects.aggregate(a=Avg('response_ms'))['a'] or 0

    sessions_qs = (
        ChatSession.objects
        .select_related('user')
        .annotate(message_count=Count('messages'))
        .order_by('-updated_at')[:10]
    )
    sessions_data = [{
        'session_id':    str(s.session_id),
        'session_short': '#' + str(s.session_id)[:8].upper(),
        'title':         s.title or '새 대화',
        'user':          s.user.get_full_name() or s.user.username,
        'message_count': s.message_count,
        'is_active':     s.updated_at >= active_cutoff,
        'updated_at':    s.updated_at.strftime('%Y-%m-%dT%H:%M:%S'),
        'chat_model':    s.chat_model or '',
    } for s in sessions_qs]

    return JsonResponse({
        'today_messages':  today_messages,
        'active_sessions': active_sessions,
        'ready_rags':      ready_rags,
        'total_chunks':    total_chunks,
        'avg_response_s':  round(avg_ms / 1000, 1) if avg_ms else 0,
        'recent_sessions': sessions_data,
    })


@login_required(login_url='/chatbot/login/')
def dashboard_charts(request):
    import datetime
    from zoneinfo import ZoneInfo
    from django.utils import timezone
    from django.db.models import Count

    # MariaDB 타임존 테이블 미설치 환경 — DB 변환 없이 Python에서 처리
    SEOUL = ZoneInfo('Asia/Seoul')
    now_seoul   = timezone.now().astimezone(SEOUL)
    today_seoul = now_seoul.date()

    def get_daily(days):
        start_local = today_seoul - datetime.timedelta(days=days - 1)
        # UTC 기준으로 충분히 넓게 fetch (타임존 경계 +1일 여유)
        since_utc = timezone.now() - datetime.timedelta(days=days + 1)
        timestamps = (
            ChatMessage.objects
            .filter(created_at__gte=since_utc)
            .values_list('created_at', flat=True)
        )
        # Python에서 서울 날짜로 변환 후 집계
        counts: dict = {}
        for ts in timestamps:
            d = ts.astimezone(SEOUL).date()
            if start_local <= d <= today_seoul:
                counts[d] = counts.get(d, 0) + 1

        day_names = ['월', '화', '수', '목', '금', '토', '일']
        result = []
        for i in range(days):
            d = start_local + datetime.timedelta(days=i)
            label = day_names[d.weekday()] if days == 7 else f'{d.day}일'
            result.append({'label': label, 'count': counts.get(d, 0)})
        return result

    cat_qs = (
        ChatMessage.objects
        .exclude(chat_model='')
        .values('chat_model')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    categories = [{'label': r['chat_model'], 'count': r['count']} for r in cat_qs]
    if not categories:
        categories = [{'label': '데이터 없음', 'count': 1}]

    return JsonResponse({
        'daily_7':    get_daily(7),
        'daily_30':   get_daily(30),
        'categories': categories,
    })


@login_required(login_url='/chatbot/login/')
def chatting_list(request):
    if not _is_admin(request.user):
        return redirect('chatbot')
    from django.db.models import Count, Q
    from django.core.paginator import Paginator

    q  = request.GET.get('q', '').strip()
    qs = (
        ChatSession.objects
        .select_related('user')
        .annotate(message_count=Count('messages'))
        .order_by('-created_at')
    )
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(username__icontains=q) | Q(chat_model__icontains=q))

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'dashboard/chatting_list.html', {
        'page_obj':    page_obj,
        'q':           q,
        'total_count': ChatSession.objects.count(),
        'active_nav':  'sessions',
    })


@login_required(login_url='/chatbot/login/')
def chatting_view(request, session_uuid):
    import json as _json
    if not _is_admin(request.user):
        return redirect('chatbot')
    session  = get_object_or_404(ChatSession, session_id=session_uuid)
    messages = list(ChatMessage.objects.filter(session=session).order_by('created_at'))
    # HTML 속성 대신 script 태그로 전달 — escapejs 이슈 방지
    _safe_escapes = {ord('<'): '\\u003C', ord('>'): '\\u003E', ord('&'): '\\u0026'}
    answers_json = _json.dumps(
        [m.answer for m in messages], ensure_ascii=False
    ).translate(_safe_escapes)
    return render(request, 'dashboard/chatting_view.html', {
        'session':      session,
        'messages':     messages,
        'answers_json': answers_json,
        'active_nav':   'sessions',
    })


@login_required(login_url='/chatbot/login/')
def chatting_count(request):
    return JsonResponse({'count': ChatSession.objects.count()})


@login_required(login_url='/chatbot/login/')
def chart_list(request):
    if not _is_admin(request.user):
        return redirect('chatbot')
    return render(request, 'dashboard/chart_list.html', {'active_nav': 'analytics'})


@login_required(login_url='/chatbot/login/')
def analytics_data(request):
    import datetime
    import re
    from collections import Counter
    from zoneinfo import ZoneInfo
    from django.utils import timezone
    from django.db.models import Count, Avg, Sum

    SEOUL = ZoneInfo('Asia/Seoul')
    now = timezone.now()
    now_seoul = now.astimezone(SEOUL)
    today_seoul = now_seoul.date()

    period = int(request.GET.get('days', 30))
    if period not in (7, 14, 30, 90):
        period = 30

    # ─── KPI 요약 ───────────────────────────────────────────
    total_messages = ChatMessage.objects.count()
    total_sessions = ChatSession.objects.count()
    error_count    = ChatMessage.objects.filter(is_error=True).count()
    error_rate     = round(error_count / total_messages * 100, 1) if total_messages else 0
    avg_ms_val     = ChatMessage.objects.aggregate(a=Avg('response_ms'))['a'] or 0
    total_tokens_val = ChatMessage.objects.aggregate(s=Sum('total_tokens'))['s'] or 0

    # ─── 일별 대화량 (period 기준) ──────────────────────────
    start_local = today_seoul - datetime.timedelta(days=period - 1)
    since_utc   = now - datetime.timedelta(days=period + 1)

    period_ts = ChatMessage.objects.filter(
        created_at__gte=since_utc
    ).values_list('created_at', flat=True)

    daily_counts = {}
    for ts in period_ts:
        d = ts.astimezone(SEOUL).date()
        if start_local <= d <= today_seoul:
            daily_counts[d] = daily_counts.get(d, 0) + 1

    daily_data = []
    for i in range(period):
        d = start_local + datetime.timedelta(days=i)
        daily_data.append({'label': d.strftime('%m/%d'), 'count': daily_counts.get(d, 0)})

    # ─── 시간대별 분포 (전체 기간) ──────────────────────────
    hourly_counts = [0] * 24
    all_ts = ChatMessage.objects.values_list('created_at', flat=True)
    for ts in all_ts:
        hourly_counts[ts.astimezone(SEOUL).hour] += 1
    hourly = [{'label': f'{h:02d}시', 'count': hourly_counts[h]} for h in range(24)]

    # ─── RAG별 사용량 ──────────────────────────────────────
    rag_usage_qs = (
        ChatMessage.objects
        .exclude(chat_model='')
        .values('chat_model')
        .annotate(count=Count('id'), avg_ms=Avg('response_ms'))
        .order_by('-count')[:10]
    )
    rag_stats = [
        {'label': r['chat_model'], 'count': r['count'], 'avg_ms': round(r['avg_ms'] or 0)}
        for r in rag_usage_qs
    ]

    # ─── 응답 시간 분포 ────────────────────────────────────
    rt_buckets = [
        ('500ms 미만',  None, 500),
        ('500ms~1초',   500,  1000),
        ('1초~3초',    1000,  3000),
        ('3초~5초',    3000,  5000),
        ('5초 이상',   5000,  None),
    ]
    rt_dist = []
    for label, low, high in rt_buckets:
        qs = ChatMessage.objects
        if low  is not None: qs = qs.filter(response_ms__gte=low)
        if high is not None: qs = qs.filter(response_ms__lt=high)
        rt_dist.append({'label': label, 'count': qs.count()})

    # ─── 인기 검색어 TOP 20 ────────────────────────────────
    STOP_WORDS = {
        '이', '가', '을', '를', '은', '는', '의', '에', '에서', '와', '과',
        '하다', '있다', '없다', '그', '것', '수', '및', '등', '또', '더',
        '안', '못', '때', '어떻게', '어떤', '무엇', '어디', '왜', '언제',
        '누구', '관련', '대해', '대한', '하는', '하고', '하여', '하면',
        '할', '한', '하지', '이고', '이며', '로', '으로', '도', '고',
        '며', '지', '면', '아', '야', '요', '죠', '네', '이다', '합니다',
        '습니다', '있나요', '알려주세요', '해주세요', '말해주세요',
    }
    questions_qs = ChatMessage.objects.values_list('question', flat=True)[:2000]
    word_freq = Counter()
    for q_text in questions_qs:
        for w in re.split(r'[\s\.,!?;:()\[\]"\'\n\r]+', q_text):
            w = w.strip()
            if len(w) >= 2 and w not in STOP_WORDS and not w.isdigit():
                word_freq[w] += 1
    top_keywords = [{'word': w, 'count': c} for w, c in word_freq.most_common(20)]

    # ─── 사용자별 활동 ─────────────────────────────────────
    user_msg_qs = (
        ChatMessage.objects
        .exclude(username='')
        .values('username')
        .annotate(msg_count=Count('id'))
        .order_by('-msg_count')[:10]
    )
    sess_map = {
        r['username']: r['sess_count']
        for r in ChatSession.objects.exclude(username='')
                  .values('username').annotate(sess_count=Count('id'))
    }
    user_stats = [
        {'username': r['username'], 'msg_count': r['msg_count'],
         'sess_count': sess_map.get(r['username'], 0)}
        for r in user_msg_qs
    ]

    # ─── RAG 성능 요약 ─────────────────────────────────────
    rag_perf = []
    for rag in RagConfig.objects.filter(is_active=True).order_by('-created_at'):
        mc = ChatMessage.objects.filter(chat_model=rag.name).count()
        am = ChatMessage.objects.filter(chat_model=rag.name).aggregate(a=Avg('response_ms'))['a'] or 0
        rag_perf.append({
            'name': rag.name,
            'status': rag.status,
            'chunk_count': rag.chunk_count,
            'total_tokens': rag.total_tokens,
            'msg_count': mc,
            'avg_ms': round(am),
        })

    return JsonResponse({
        'period': period,
        'summary': {
            'total_messages':  total_messages,
            'total_sessions':  total_sessions,
            'error_rate':      error_rate,
            'avg_response_ms': round(avg_ms_val),
            'total_tokens':    total_tokens_val,
        },
        'daily':        daily_data,
        'hourly':       hourly,
        'rag_stats':    rag_stats,
        'rt_dist':      rt_dist,
        'top_keywords': top_keywords,
        'user_stats':   user_stats,
        'rag_perf':     rag_perf,
    })


@login_required(login_url='/chatbot/login/')
def doc_list(request):
    if not _is_admin(request.user):
        return redirect('chatbot')
    from django.db.models import Q
    q  = request.GET.get('q', '').strip()
    qs = RagConfig.objects.select_related('created_by').order_by('-created_at')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(source_file_name__icontains=q) | Q(description__icontains=q))
    return render(request, 'dashboard/doc_list.html', {
        'docs':       qs,
        'q':          q,
        'total':      RagConfig.objects.count(),
        'active_nav': 'documents',
    })


@login_required(login_url='/chatbot/login/')
def doc_detail(request, doc_id):
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    doc = get_object_or_404(RagConfig, id=doc_id)

    def fmt_size(b):
        for u in ('B', 'KB', 'MB', 'GB'):
            if b < 1024:
                return f"{b:.1f} {u}"
            b /= 1024
        return f"{b:.1f} TB"

    def fmt_ms(ms):
        if ms >= 60000:
            return f"{ms//60000}분 {(ms%60000)//1000}초"
        if ms >= 1000:
            return f"{ms/1000:.1f}초"
        return f"{ms}ms" if ms else "-"

    return JsonResponse({
        'id':               doc.id,
        'name':             doc.name,
        'description':      doc.description or '-',
        'status':           doc.status,
        'status_display':   doc.get_status_display(),
        'is_active':        doc.is_active,
        'source_file_name': doc.source_file_name or '-',
        'source_file_type': doc.source_file_type,
        'source_file_size': fmt_size(doc.source_file_size),
        'result_file_path': doc.result_file_path or '-',
        'embedding_model':  doc.embedding_model,
        'llm_model':        doc.llm_model,
        'chunk_size':       doc.chunk_size,
        'chunk_overlap':    doc.chunk_overlap,
        'top_k':            doc.top_k,
        'chunk_count':      doc.chunk_count,
        'total_tokens':     doc.total_tokens,
        'build_time':       fmt_ms(doc.build_time_ms),
        'error_message':    doc.error_message or '-',
        'created_by':       (doc.created_by.get_full_name() or doc.created_by.username) if doc.created_by else '-',
        'created_at':       doc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at':       doc.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


@ensure_csrf_cookie
@login_required(login_url='/chatbot/login/')
def chatbot(request):
    return render(request, 'dashboard/chat.html')


# ─────────────────────────────────────────────
#  사용자 관리 CRUD
# ─────────────────────────────────────────────

def _user_to_dict(u):
    return {
        'id':          u.id,
        'username':    u.username,
        'email':       u.email,
        'first_name':  u.first_name,
        'last_name':   u.last_name,
        'full_name':   u.get_full_name() or u.username,
        'is_superuser': u.is_superuser,
        'is_staff':    u.is_staff,
        'is_active':   u.is_active,
        'date_joined': u.date_joined.strftime('%Y-%m-%d') if u.date_joined else '',
        'last_login':  u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else '없음',
    }


@login_required(login_url='/chatbot/login/')
def user_list(request):
    if not _is_admin(request.user):
        return redirect('chatbot')

    # AJAX 목록 조회
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        users = [_user_to_dict(u) for u in User.objects.all().order_by('-date_joined')]
        return JsonResponse({'users': users})

    ctx = {
        'active_nav': 'users',
        'total_users':  User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users':  User.objects.filter(is_staff=True).count(),
        'super_users':  User.objects.filter(is_superuser=True).count(),
    }
    return render(request, 'dashboard/user_list.html', ctx)


@login_required(login_url='/chatbot/login/')
def user_add(request):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 메서드'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청'}, status=400)

    username   = data.get('username', '').strip()
    email      = data.get('email', '').strip()
    password   = data.get('password', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name  = data.get('last_name', '').strip()
    is_staff      = bool(data.get('is_staff', False))
    is_superuser  = bool(data.get('is_superuser', False))

    if not username or not email or not password:
        return JsonResponse({'success': False, 'error': '아이디, 이메일, 비밀번호는 필수입니다.'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': '이미 사용 중인 아이디입니다.'}, status=400)
    if User.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': '이미 사용 중인 이메일입니다.'}, status=400)

    user = User.objects.create_user(
        username=username, email=email, password=password,
        first_name=first_name, last_name=last_name,
    )
    user.is_staff      = is_staff
    user.is_superuser  = is_superuser
    user.save()

    return JsonResponse({'success': True, 'user': _user_to_dict(user)})


@login_required(login_url='/chatbot/login/')
def user_edit(request, user_id):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 메서드'}, status=405)

    target = get_object_or_404(User, id=user_id)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청'}, status=400)

    email      = data.get('email', '').strip()
    first_name = data.get('first_name', '').strip()
    last_name  = data.get('last_name', '').strip()
    is_staff      = bool(data.get('is_staff', False))
    is_superuser  = bool(data.get('is_superuser', False))
    is_active     = bool(data.get('is_active', True))
    password      = data.get('password', '').strip()

    if email and User.objects.filter(email=email).exclude(id=user_id).exists():
        return JsonResponse({'success': False, 'error': '이미 사용 중인 이메일입니다.'}, status=400)

    if email:
        target.email = email
    target.first_name   = first_name
    target.last_name    = last_name
    target.is_staff     = is_staff
    target.is_superuser = is_superuser
    target.is_active    = is_active
    if password:
        target.set_password(password)
    target.save()

    return JsonResponse({'success': True, 'user': _user_to_dict(target)})


@login_required(login_url='/chatbot/login/')
def user_delete(request, user_id):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 메서드'}, status=405)

    target = get_object_or_404(User, id=user_id)

    if target == request.user:
        return JsonResponse({'success': False, 'error': '자기 자신은 삭제할 수 없습니다.'}, status=400)
    if target.is_superuser and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '슈퍼관리자는 슈퍼관리자만 삭제할 수 있습니다.'}, status=403)

    target.delete()
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
#  로그 관리
# ─────────────────────────────────────────────


@login_required(login_url='/chatbot/login/')
def log_history(request):
    if not _is_admin(request.user):
        return redirect('chatbot')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logs = LoginLog.objects.all().order_by('-created_at')[:1000]
        data = [{
            'id':             l.id,
            'username':       l.username,
            'email':          l.email,
            'action':         l.action,
            'action_display': l.get_action_display(),
            'client_ip':      l.client_ip or '-',
            'user_agent':     l.user_agent,
            'is_admin':       l.is_admin,
            'created_at':     l.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        } for l in logs]
        return JsonResponse({'logs': data})

    ctx = {
        'active_nav':   'logs',
        'total_logs':   LoginLog.objects.count(),
        'login_count':  LoginLog.objects.filter(action=LoginLog.ACTION_LOGIN).count(),
        'fail_count':   LoginLog.objects.filter(action=LoginLog.ACTION_FAIL).count(),
        'logout_count': LoginLog.objects.filter(action=LoginLog.ACTION_LOGOUT).count(),
    }
    return render(request, 'dashboard/loghistory.html', ctx)


# ─────────────────────────────────────────────
#  RAG 설정 CRUD
# ─────────────────────────────────────────────

def _detect_file_type(filename):
    ext = Path(filename).suffix.lower().lstrip('.')
    return {'pdf': 'pdf', 'docx': 'docx', 'txt': 'txt', 'md': 'md',
            'csv': 'csv', 'xlsx': 'xlsx', 'html': 'html'}.get(ext, 'other')


def _rag_to_dict(r):
    return {
        'id': r.id,
        'rag_id': str(r.rag_id),
        'name': r.name,
        'description': r.description,
        'status': r.status,
        'status_display': r.get_status_display(),
        'source_file_path': r.source_file_path,
        'source_file_name': r.source_file_name,
        'source_file_type': r.source_file_type,
        'source_file_size_display': r.source_file_size_display(),
        'result_file_path': r.result_file_path,
        'embedding_model': r.embedding_model,
        'llm_model': r.llm_model,
        'chunk_size': r.chunk_size,
        'chunk_overlap': r.chunk_overlap,
        'top_k': r.top_k,
        'chunk_count': r.chunk_count,
        'build_time_ms': r.build_time_ms,
        'error_message': r.error_message,
        'is_active': r.is_active,
        'created_by': r.created_by.get_full_name() or r.created_by.username if r.created_by else '-',
        'client_ip': r.client_ip or '-',
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '',
        'updated_at': r.updated_at.strftime('%Y-%m-%d %H:%M') if r.updated_at else '',
    }


@login_required(login_url='/chatbot/login/')
def rag_setting(request):
    if not _is_admin(request.user):
        return redirect('chatbot')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rags = [_rag_to_dict(r) for r in RagConfig.objects.all().order_by('-created_at')]
        return JsonResponse({'rags': rags})
    ctx = {
        'active_nav': 'rag_setting',
        'total_count':      RagConfig.objects.count(),
        'ready_count':      RagConfig.objects.filter(status='ready').count(),
        'processing_count': RagConfig.objects.filter(status='processing').count(),
        'error_count':      RagConfig.objects.filter(status='error').count(),
    }
    return render(request, 'dashboard/rag_setting.html', ctx)


@login_required(login_url='/chatbot/login/')
def rag_add(request):
    if not _is_admin(request.user):
        return redirect('chatbot')
    if request.method == 'POST':
        name          = request.POST.get('name', '').strip()
        description   = request.POST.get('description', '').strip()
        chunk_size    = int(request.POST.get('chunk_size', 800))
        chunk_overlap = int(request.POST.get('chunk_overlap', 100))
        top_k         = int(request.POST.get('top_k', 5))
        embed_model   = request.POST.get('embedding_model', 'BAAI/bge-m3').strip()
        llm_model     = request.POST.get('llm_model', 'gemini-2.5-flash').strip()
        uploaded      = request.FILES.get('source_file')
        if not name:
            return JsonResponse({'success': False, 'error': 'RAG명을 입력해 주세요.'}, status=400)
        if not uploaded:
            return JsonResponse({'success': False, 'error': '파일을 선택해 주세요.'}, status=400)
        from django.conf import settings as _settings
        rag_uuid = RagConfig._meta.get_field('rag_id').default()
        save_dir = Path(_settings.BASE_DIR) / 'source' / str(rag_uuid)
        save_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(uploaded.name).name
        with open(save_dir / safe_name, 'wb') as f:
            for chunk in uploaded.chunks():
                f.write(chunk)
        rag = RagConfig.objects.create(
            rag_id=rag_uuid, name=name, description=description,
            status=RagConfig.STATUS_PENDING,
            source_file_path=f'source/{rag_uuid}/{safe_name}',
            source_file_name=safe_name,
            source_file_size=uploaded.size,
            source_file_type=_detect_file_type(safe_name),
            embedding_model=embed_model, llm_model=llm_model,
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, top_k=top_k,
            created_by=request.user, client_ip=_get_client_ip(request),
        )
        return JsonResponse({'success': True, 'rag': _rag_to_dict(rag)})
    return render(request, 'dashboard/rag_add.html', {'active_nav': 'rag_setting'})


@login_required(login_url='/chatbot/login/')
def rag_edit(request, rag_id):
    if not _is_admin(request.user):
        return redirect('chatbot')
    rag = get_object_or_404(RagConfig, id=rag_id)
    if request.method == 'POST':
        name          = request.POST.get('name', '').strip()
        description   = request.POST.get('description', '').strip()
        chunk_size    = int(request.POST.get('chunk_size', rag.chunk_size))
        chunk_overlap = int(request.POST.get('chunk_overlap', rag.chunk_overlap))
        top_k         = int(request.POST.get('top_k', rag.top_k))
        embed_model   = request.POST.get('embedding_model', rag.embedding_model).strip()
        llm_model     = request.POST.get('llm_model', rag.llm_model).strip()
        is_active     = request.POST.get('is_active', 'true') == 'true'
        uploaded      = request.FILES.get('source_file')
        if not name:
            return JsonResponse({'success': False, 'error': 'RAG명을 입력해 주세요.'}, status=400)
        if uploaded:
            from django.conf import settings as _settings
            save_dir = Path(_settings.BASE_DIR) / 'source' / str(rag.rag_id)
            save_dir.mkdir(parents=True, exist_ok=True)
            safe_name = Path(uploaded.name).name
            with open(save_dir / safe_name, 'wb') as f:
                for chunk in uploaded.chunks():
                    f.write(chunk)
            rag.source_file_path = f'source/{rag.rag_id}/{safe_name}'
            rag.source_file_name = safe_name
            rag.source_file_size = uploaded.size
            rag.source_file_type = _detect_file_type(safe_name)
            rag.status = RagConfig.STATUS_PENDING
        rag.name = name
        rag.description = description
        rag.chunk_size = chunk_size
        rag.chunk_overlap = chunk_overlap
        rag.top_k = top_k
        rag.embedding_model = embed_model
        rag.llm_model = llm_model
        rag.is_active = is_active
        rag.save()
        return JsonResponse({'success': True, 'rag': _rag_to_dict(rag)})
    return render(request, 'dashboard/rag_edit.html', {
        'active_nav': 'rag_setting', 'rag': rag,
    })


@login_required(login_url='/chatbot/login/')
def rag_delete(request, rag_id):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 메서드'}, status=405)
    rag = get_object_or_404(RagConfig, id=rag_id)
    from django.conf import settings as _settings
    for d in [Path(_settings.BASE_DIR) / 'source' / str(rag.rag_id),
              Path(_settings.BASE_DIR) / 'rag_db' / str(rag.rag_id)]:
        if d.exists():
            shutil.rmtree(d)
    rag.delete()
    return JsonResponse({'success': True})


@login_required(login_url='/chatbot/login/')
def rag_build(request, rag_id):
    if not _is_admin(request.user):
        return JsonResponse({'success': False, 'error': '권한이 없습니다.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 메서드'}, status=405)
    rag = get_object_or_404(RagConfig, id=rag_id)
    if rag.status == RagConfig.STATUS_PROCESSING:
        return JsonResponse({'success': False, 'error': '이미 빌드 중입니다.'}, status=400)
    from .rag_builder import build_rag_async
    build_rag_async(rag.id)
    return JsonResponse({'success': True, 'status': 'processing'})


@login_required(login_url='/chatbot/login/')
def rag_build_status(request, rag_id):
    rag = get_object_or_404(RagConfig, id=rag_id)
    return JsonResponse({
        'status': rag.status,
        'status_display': rag.get_status_display(),
        'chunk_count': rag.chunk_count,
        'build_time_ms': rag.build_time_ms,
        'error_message': rag.error_message,
    })


# ─────────────────────────────────────────────
#  채팅 API
# ─────────────────────────────────────────────

@login_required(login_url='/chatbot/login/')
def chat_rags(request):
    """준비 완료된 RAG 목록 반환 (채팅 드롭다운용)"""
    rags = RagConfig.objects.filter(status='ready', is_active=True).order_by('-created_at')
    data = [{
        'id':          r.id,
        'name':        r.name,
        'description': r.description,
        'llm_model':   r.llm_model,
        'chunk_count': r.chunk_count,
    } for r in rags]
    return JsonResponse({'rags': data})


@login_required(login_url='/chatbot/login/')
def chat_api(request):
    """RAG 채팅 처리 — 결과를 ChatSession/ChatMessage에 저장"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '잘못된 메서드'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'success': False, 'error': '잘못된 요청'}, status=400)

    question     = data.get('question', '').strip()
    rag_id       = data.get('rag_id')
    session_uuid = data.get('session_id', '')

    if not question:
        return JsonResponse({'success': False, 'error': '질문을 입력해 주세요.'}, status=400)
    if not rag_id:
        return JsonResponse({'success': False, 'error': 'RAG를 선택해 주세요.'}, status=400)

    rag_config = get_object_or_404(RagConfig, id=rag_id, status='ready', is_active=True)

    # ── 세션 조회 or 신규 생성 ────────────────────────────────────────
    session = None
    if session_uuid:
        import uuid as _uuid
        try:
            session = ChatSession.objects.filter(
                session_id=_uuid.UUID(str(session_uuid)), user=request.user
            ).first()
        except (ValueError, AttributeError):
            pass

    if not session:
        session = ChatSession.objects.create(
            user=request.user,
            username=request.user.username,
            chat_model=rag_config.name,
            title=question[:100],
            client_ip=_get_client_ip(request),
        )

    # ── RAG 실행 ─────────────────────────────────────────────────────
    import sys
    import time
    from pathlib import Path
    from django.conf import settings as _settings

    BASE_DIR = Path(_settings.BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    from rag_bge_m3_class_table import RagBgeM3

    db_path  = str(BASE_DIR / rag_config.result_file_path)
    pdf_path = str(BASE_DIR / rag_config.source_file_path)

    rag_instance = RagBgeM3(
        pdf_path=pdf_path,
        db_path=db_path,
        chunk_size=rag_config.chunk_size,
        chunk_overlap=rag_config.chunk_overlap,
        search_k=rag_config.top_k,
        llm_model=rag_config.llm_model,
    )

    start    = time.time()
    is_error = False
    answer   = ''

    try:
        llm       = rag_instance.get_llm()
        retriever = rag_instance.load_retriever()
        answer    = rag_instance.runnable_lambda(
            retriever, llm, question, label=rag_config.name
        )
    except Exception as exc:
        answer   = f'오류가 발생했습니다: {str(exc)}'
        is_error = True

    elapsed_ms = int((time.time() - start) * 1000)

    # ── DB 저장 ───────────────────────────────────────────────────────
    msg = ChatMessage.objects.create(
        session=session,
        chat_model=rag_config.name,
        user=request.user,
        username=request.user.username,
        question=question,
        answer=answer,
        response_ms=elapsed_ms,
        is_error=is_error,
        client_ip=_get_client_ip(request),
    )

    return JsonResponse({
        'success':    True,
        'answer':     answer,
        'session_id': str(session.session_id),
        'message_id': str(msg.message_id),
        'response_ms': elapsed_ms,
        'is_error':   is_error,
    })


@login_required(login_url='/chatbot/login/')
def chat_sessions(request):
    """사용자의 채팅 세션 목록 반환 (사이드바 대화 목록용)"""
    sessions = (
        ChatSession.objects
        .filter(user=request.user)
        .order_by('-updated_at')[:100]
    )
    data = [{
        'session_id':    str(s.session_id),
        'title':         s.title or '새 대화',
        'chat_model':    s.chat_model,
        'message_count': s.messages.count(),
        'created_at':    s.created_at.strftime('%Y-%m-%d %H:%M'),
        'updated_at':    s.updated_at.strftime('%Y-%m-%d %H:%M'),
    } for s in sessions]
    return JsonResponse({'sessions': data})


@login_required(login_url='/chatbot/login/')
def chat_session_messages(request, session_uuid):
    """특정 세션의 메시지 전체 반환 (대화 복원용)"""
    session = get_object_or_404(ChatSession, session_id=session_uuid, user=request.user)
    messages = ChatMessage.objects.filter(session=session).order_by('created_at')
    return JsonResponse({
        'session': {
            'session_id': str(session.session_id),
            'title':      session.title or '새 대화',
            'chat_model': session.chat_model,
        },
        'messages': [{
            'message_id':  str(m.message_id),
            'question':    m.question,
            'answer':      m.answer,
            'response_ms': m.response_ms,
            'is_error':    m.is_error,
            'created_at':  m.created_at.strftime('%Y-%m-%d %H:%M'),
        } for m in messages],
    })
