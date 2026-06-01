import os
import glob
import time
import threading

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.utils import timezone
from ultralytics import YOLO

import cv2
from .faiss_face_recognition_py38 import FaceRecognitionFAISS

# ── YOLO 모델 (서버 시작 시 1회 로드) ──────────────────────────────────────
model = YOLO("yolo11s.pt")
model.export(format="onnx")
onnx_model = YOLO("yolo11s.onnx")

# ── 실시간 인식 전역 상태 ──────────────────────────────────────────────────
_state_lock = threading.Lock()

_recognition_state: dict = {
    'status':      'STANDBY',   # STANDBY | GRANTED | DENIED
    'name':        '',
    'name_en':     '',
    'employee_id': '',
    'department':  '',
    'role':        '',
    'access_level': None,
    'photo_url':   '',
    'confidence':  0.0,
    'timestamp':   '',
}

_last_log_time: dict = {}   # name_en → last AccessLog 생성 시각(time.time)
_LOG_COOLDOWN   = 30        # 동일 인물 재기록 간격(초)


def _update_state(detail: dict):
    """스트림 스레드에서 호출: 인식 결과로 전역 상태와 AccessLog를 갱신한다."""
    global _recognition_state

    from .models import Employee, AccessLog

    name_en    = detail['name']
    confidence = detail['confidence']
    distance   = detail['distance']
    now_ts     = timezone.now().strftime('%H:%M:%S')
    now_t      = time.time()

    with _state_lock:
        if name_en == 'unknown':
            _recognition_state = {
                'status':       'DENIED',
                'name':         'Unknown',
                'name_en':      '',
                'employee_id':  '',
                'department':   '',
                'role':         '',
                'access_level': None,
                'photo_url':    '',
                'confidence':   confidence,
                'timestamp':    now_ts,
            }
            # 30초 쿨다운으로 AccessLog 기록
            if now_t - _last_log_time.get('unknown', 0) >= _LOG_COOLDOWN:
                _last_log_time['unknown'] = now_t
                try:
                    AccessLog.objects.create(
                        employee=None,
                        recognized_name='',
                        direction=AccessLog.Direction.IN,
                        match_confidence=confidence / 100,
                        distance=distance,
                        encoder='dlib_128',
                        status=AccessLog.Status.DENIED,
                    )
                except Exception:
                    pass
        else:
            try:
                emp = Employee.objects.select_related().get(name_en=name_en)
                _recognition_state = {
                    'status':       'GRANTED',
                    'name':         emp.name,
                    'name_en':      emp.name_en,
                    'employee_id':  emp.employee_id,
                    'department':   emp.department,
                    'role':         emp.role or '',
                    'access_level': emp.access_level,
                    'photo_url':    emp.photo.url if emp.photo else '',
                    'confidence':   confidence,
                    'timestamp':    now_ts,
                }
                if now_t - _last_log_time.get(name_en, 0) >= _LOG_COOLDOWN:
                    _last_log_time[name_en] = now_t
                    try:
                        AccessLog.objects.create(
                            employee=emp,
                            recognized_name=emp.name,
                            direction=AccessLog.Direction.IN,
                            match_confidence=confidence / 100,
                            distance=distance,
                            encoder='dlib_128',
                            status=AccessLog.Status.GRANTED,
                        )
                    except Exception:
                        pass
            except Employee.DoesNotExist:
                # Employee DB에 없음 → Manager 모델에서 검색
                from backoffice.models import Manager as ManagerModel
                display_name = name_en
                display_photo = ''
                try:
                    mgr = ManagerModel.objects.get(name_en=name_en)
                    display_name  = mgr.name
                    display_photo = mgr.photo.url if mgr.photo else ''
                    _recognition_state = {
                        'status':       'GRANTED',
                        'name':         mgr.name,
                        'name_en':      mgr.name_en,
                        'employee_id':  mgr.username,
                        'department':   '관리자',
                        'role':         'Manager',
                        'access_level': 3,
                        'photo_url':    display_photo,
                        'confidence':   confidence,
                        'timestamp':    now_ts,
                    }
                except ManagerModel.DoesNotExist:
                    _recognition_state = {
                        'status':       'GRANTED',
                        'name':         name_en,
                        'name_en':      name_en,
                        'employee_id':  '',
                        'department':   '',
                        'role':         '',
                        'access_level': None,
                        'photo_url':    '',
                        'confidence':   confidence,
                        'timestamp':    now_ts,
                    }
                # AccessLog 생성 (employee=None, recognized_name으로 이름 보존)
                if now_t - _last_log_time.get(name_en, 0) >= _LOG_COOLDOWN:
                    _last_log_time[name_en] = now_t
                    try:
                        AccessLog.objects.create(
                            employee=None,
                            recognized_name=display_name,
                            direction=AccessLog.Direction.IN,
                            match_confidence=confidence / 100,
                            distance=distance,
                            encoder='dlib_128',
                            status=AccessLog.Status.GRANTED,
                        )
                    except Exception:
                        pass


# ── 뷰 ─────────────────────────────────────────────────────────────────────
def index(request):
    return render(request, "cctv/main.html")


def video_feed(request):
    return StreamingHttpResponse(
        stream(request),
        content_type='multipart/x-mixed-replace;boundary=frame',
    )


def full_log(request):
    """전체 출입 기록 — 페이지네이션 + 상태 필터."""
    from .models import AccessLog
    from datetime import date, datetime

    filter_type = request.GET.get('filter', 'all')
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    per_page = 20

    qs = AccessLog.objects.select_related('employee').order_by('-timestamp')
    if filter_type == 'granted':
        qs = qs.filter(status=AccessLog.Status.GRANTED)
    elif filter_type == 'denied':
        qs = qs.filter(status=AccessLog.Status.DENIED)

    total       = qs.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page        = min(page, total_pages)
    start       = (page - 1) * per_page
    page_qs     = qs[start:start + per_page]

    logs = []
    for idx, log in enumerate(page_qs):
        emp      = log.employee
        fallback = log.recognized_name or 'Unknown'
        logs.append({
            'seq':         total - start - idx,
            'name':        emp.name        if emp else fallback,
            'name_en':     emp.name_en     if emp else '',
            'employee_id': emp.employee_id if emp else '',
            'department':  emp.department  if emp else '',
            'photo_url':   emp.photo.url   if (emp and emp.photo) else '',
            'direction':   log.direction,
            'confidence':  round(log.match_confidence * 100, 1),
            'status':      log.status,
            'timestamp':   timezone.localtime(log.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
        })

    # 오늘 통계 (히어로 섹션용)
    today_start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    today_qs    = AccessLog.objects.filter(timestamp__gte=today_start)
    today = {
        'total':   today_qs.count(),
        'granted': today_qs.filter(status=AccessLog.Status.GRANTED).count(),
        'denied':  today_qs.filter(status=AccessLog.Status.DENIED).count(),
    }

    return JsonResponse({
        'logs':        logs,
        'total':       total,
        'page':        page,
        'per_page':    per_page,
        'total_pages': total_pages,
        'today':       today,
    })


def status(request):
    """현재 인식 상태 + 최근 5분 로그를 JSON으로 반환 (프론트엔드 폴링용)."""
    from .models import AccessLog
    from datetime import timedelta

    with _state_lock:
        current = dict(_recognition_state)

    five_min_ago = timezone.now() - timedelta(minutes=5)
    logs = (
        AccessLog.objects
        .filter(timestamp__gte=five_min_ago)
        .select_related('employee')
        .order_by('-timestamp')[:10]
    )

    log_data = []
    for log in logs:
        emp = log.employee
        fallback_name = log.recognized_name or 'Unknown'
        log_data.append({
            'name':        emp.name        if emp else fallback_name,
            'name_en':     emp.name_en     if emp else '',
            'employee_id': emp.employee_id if emp else '',
            'department':  emp.department  if emp else '',
            'photo_url':   emp.photo.url   if (emp and emp.photo) else '',
            'direction':   log.direction,
            'confidence':  round(log.match_confidence * 100, 1),
            'status':      log.status,
            'timestamp':   timezone.localtime(log.timestamp).strftime('%H:%M:%S'),
        })

    return JsonResponse({'current': current, 'logs': log_data})


# ── MJPEG 스트림 ──────────────────────────────────────────────────────────
def stream(request):
    cap = cv2.VideoCapture(0)

    fr = FaceRecognitionFAISS(
        org_data_path="./dataset/org_data",
        dataset_path="./dataset/data",
        train_dir="./dataset/train",
        test_tmp_path="./dataset/test/test1.jpg",
        face_margin=20,
        top_k=5,
        min_vote=3,
    )

    loaded_bin = ''

    def _load_latest():
        nonlocal loaded_bin
        bins = sorted(glob.glob("./dataset/train/face_*.bin"))
        if not bins:
            return False
        latest = bins[-1]
        if latest != loaded_bin:
            try:
                fr.load_model(latest)
                loaded_bin = latest
            except Exception as e:
                print(f"[stream] 모델 로드 실패: {e}")
                return loaded_bin != ''
        return True

    if not _load_latest():
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\nContent-type:image/jpeg\r\n\r\n'
                   + image_bytes + b'\r\n')
        cap.release()
        return

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        if frame_count % 300 == 0:
            _load_latest()

        results = onnx_model(frame, classes=0)
        df      = results[0].to_df()

        if len(df) == 1:
            detail = fr.predict_numpy_detail(frame)
            _update_state(detail)
            frame  = results[0].plot()
        else:
            with _state_lock:
                if _recognition_state['status'] != 'STANDBY':
                    _recognition_state.update({
                        'status': 'STANDBY', 'name': '', 'name_en': '',
                        'employee_id': '', 'department': '', 'role': '',
                        'access_level': None, 'photo_url': '',
                        'confidence': 0.0, 'timestamp': '',
                    })

        image_bytes = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\nContent-type:image/jpeg\r\n\r\n'
               + image_bytes + b'\r\n')

    cap.release()
