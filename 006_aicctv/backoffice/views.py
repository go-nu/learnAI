import os
import shutil
import traceback
import functools
import threading
import time

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.conf import settings

from .models import Manager
from cctv.models import Employee


# ── 로그인 데코레이터 ──────────────────────────────────────────────────────
def login_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'manager_id' not in request.session:
            return redirect('bo_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_manager(request):
    return Manager.objects.get(id=request.session['manager_id'])


# ── FAISS 데이터셋 경로에 사진 복사 ─────────────────────────────────────
def _copy_to_dataset(media_relative_path: str, pk: int, name: str, name_en: str):
    """media 경로의 사진을 org_data/<name_en>/ 와 data/<name_en>/ 두 곳에 복사한다."""
    if not name_en:
        return
    src = os.path.join(settings.MEDIA_ROOT, str(media_relative_path))
    if not os.path.exists(src):
        return
    ext = os.path.splitext(src)[1] or '.jpg'
    filename = f"{pk}_{name}_{name_en}{ext}"
    for subdir in ('org_data', 'data'):
        dst_dir = os.path.join(settings.BASE_DIR, 'dataset', subdir, name_en)
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, os.path.join(dst_dir, filename))


# ── FAISS 재학습 ───────────────────────────────────────────────────────────
_retrain_lock = threading.Lock()
_retrain_state: dict = {
    'status':      'idle',   # idle | running | done | error
    'message':     '',
    'started_at':  '',
    'finished_at': '',
}


def _run_retrain():
    from cctv.faiss_face_recognition_py38 import FaceRecognitionFAISS

    global _retrain_state
    with _retrain_lock:
        _retrain_state.update({
            'status':      'running',
            'message':     '얼굴 인코딩 및 FAISS 인덱스 학습 중...',
            'started_at':  time.strftime('%H:%M:%S'),
            'finished_at': '',
        })
    try:
        fr = FaceRecognitionFAISS(
            org_data_path=os.path.join(settings.BASE_DIR, 'dataset', 'org_data'),
            dataset_path=os.path.join(settings.BASE_DIR, 'dataset', 'data'),
            train_dir=os.path.join(settings.BASE_DIR, 'dataset', 'train'),
            test_tmp_path=os.path.join(settings.BASE_DIR, 'dataset', 'test', 'test1.jpg'),
            face_margin=20,
            top_k=5,
            min_vote=3,
        )
        fr.train()
        bin_name = f"face_{time.strftime('%Y%m%d')}.bin"
        with _retrain_lock:
            _retrain_state.update({
                'status':      'done',
                'message':     f'학습 완료 → {bin_name} 저장됨',
                'finished_at': time.strftime('%H:%M:%S'),
            })
    except Exception:
        with _retrain_lock:
            _retrain_state.update({
                'status':      'error',
                'message':     traceback.format_exc(),
                'finished_at': time.strftime('%H:%M:%S'),
            })


# ── 로그인 ─────────────────────────────────────────────────────────────────
def login_view(request):
    if 'manager_id' in request.session:
        return redirect('bo_dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        try:
            manager = Manager.objects.get(username=username)
            if manager.check_password(password):
                request.session['manager_id']    = manager.id
                request.session['manager_name']  = manager.name
                request.session['manager_photo'] = manager.photo.url if manager.photo else ''
                return redirect('bo_dashboard')
            else:
                error = '아이디 또는 비밀번호가 올바르지 않습니다.'
        except Manager.DoesNotExist:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'

    return render(request, 'backoffice/login.html', {'error': error})


# ── 로그아웃 ───────────────────────────────────────────────────────────────
def logout_view(request):
    request.session.flush()
    return redirect('bo_login')


# ── 대시보드 ───────────────────────────────────────────────────────────────
@login_required
def dashboard(request):
    manager    = _get_manager(request)
    total_emp  = Employee.objects.count()
    dept_stats = {}
    for emp in Employee.objects.values('department'):
        dept = emp['department']
        dept_stats[dept] = dept_stats.get(dept, 0) + 1

    return render(request, 'backoffice/dashboard.html', {
        'manager':    manager,
        'total_emp':  total_emp,
        'dept_stats': dept_stats,
    })


# ── 프로필 수정 ────────────────────────────────────────────────────────────
@login_required
def profile(request):
    manager = _get_manager(request)
    error   = None
    success = None

    if request.method == 'POST':
        manager.name    = request.POST.get('name', '').strip()
        manager.name_en = request.POST.get('name_en', '').strip()
        manager.email   = request.POST.get('email', '').strip()
        manager.phone   = request.POST.get('phone', '').strip()

        new_pw     = request.POST.get('new_password', '').strip()
        confirm_pw = request.POST.get('confirm_password', '').strip()
        photo      = request.FILES.get('photo')

        if new_pw:
            if new_pw != confirm_pw:
                error = '새 비밀번호가 일치하지 않습니다.'
            else:
                manager.set_password(new_pw)

        if not error:
            try:
                if photo:
                    manager.photo = photo
                manager.save()
                # CCTV 데이터셋에 사진 복사 (영문 이름이 있을 때)
                if photo and manager.name_en:
                    _copy_to_dataset(manager.photo, manager.pk, manager.name, manager.name_en)
                # 세션 갱신
                request.session['manager_name']  = manager.name
                request.session['manager_photo'] = manager.photo.url if manager.photo else ''
                success = '프로필이 성공적으로 수정되었습니다.'
            except Exception:
                error = f'저장 중 오류가 발생했습니다: {traceback.format_exc()}'

    return render(request, 'backoffice/profile.html', {
        'manager': manager,
        'error':   error,
        'success': success,
    })


# ── 직원 목록 ──────────────────────────────────────────────────────────────
@login_required
def employee_list(request):
    q         = request.GET.get('q', '').strip()
    employees = Employee.objects.all().order_by('employee_id')
    if q:
        from django.db.models import Q
        employees = employees.filter(
            Q(name__icontains=q) | Q(employee_id__icontains=q) | Q(department__icontains=q)
        )

    return render(request, 'backoffice/employee_list.html', {
        'manager':   _get_manager(request),
        'employees': employees,
        'q':         q,
    })


# ── 직원 추가 ──────────────────────────────────────────────────────────────
@login_required
def employee_create(request):
    manager = _get_manager(request)
    error   = None

    if request.method == 'POST':
        emp_id     = request.POST.get('employee_id', '').strip()
        name       = request.POST.get('name', '').strip()
        name_en    = request.POST.get('name_en', '').strip()
        department = request.POST.get('department', '').strip()
        role       = request.POST.get('role', '').strip()
        access_lvl = int(request.POST.get('access_level', 1))
        photo      = request.FILES.get('photo')

        if not emp_id or not name or not department:
            error = '사원번호, 이름, 부서는 필수 입력 항목입니다.'
        elif Employee.objects.filter(employee_id=emp_id).exists():
            error = f'사원번호 [{emp_id}]는 이미 등록되어 있습니다.'
        else:
            try:
                employee = Employee(
                    employee_id=emp_id, name=name, name_en=name_en,
                    department=department, role=role, access_level=access_lvl,
                )
                if photo:
                    employee.photo = photo
                employee.save()
                if photo and name_en:
                    _copy_to_dataset(employee.photo, employee.pk, name, name_en)
                return redirect('bo_employee_list')
            except Exception:
                error = f'저장 중 오류가 발생했습니다.\n{traceback.format_exc()}'

    p = request.POST
    return render(request, 'backoffice/employee_form.html', {
        'manager':   manager,
        'mode':      'create',
        'error':     error,
        'form_data': {
            'employee_id': p.get('employee_id', ''),
            'name':        p.get('name', ''),
            'name_en':     p.get('name_en', ''),
            'department':  p.get('department', ''),
            'role':        p.get('role', ''),
            'access_level': p.get('access_level', '1'),
        },
    })


# ── 직원 수정 ──────────────────────────────────────────────────────────────
@login_required
def employee_edit(request, pk):
    manager  = _get_manager(request)
    employee = get_object_or_404(Employee, pk=pk)
    error    = None

    if request.method == 'POST':
        try:
            new_emp_id = request.POST.get('employee_id', '').strip()
            name       = request.POST.get('name', '').strip()
            name_en    = request.POST.get('name_en', '').strip()
            department = request.POST.get('department', '').strip()
            role       = request.POST.get('role', '').strip()
            access_lvl = int(request.POST.get('access_level', 1))
            photo      = request.FILES.get('photo')

            if not new_emp_id or not name or not department:
                error = '사원번호, 이름, 부서는 필수 입력 항목입니다.'
            elif Employee.objects.filter(employee_id=new_emp_id).exclude(pk=pk).exists():
                error = f'사원번호 [{new_emp_id}]는 이미 다른 직원에게 사용 중입니다.'
            else:
                employee.employee_id  = new_emp_id
                employee.name         = name
                employee.name_en      = name_en
                employee.department   = department
                employee.role         = role
                employee.access_level = access_lvl
                if photo:
                    employee.photo = photo
                employee.save()
                if photo and name_en:
                    _copy_to_dataset(employee.photo, employee.pk, name, name_en)
                return redirect('bo_employee_list')
        except Exception:
            error = f'저장 중 오류가 발생했습니다.\n{traceback.format_exc()}'

    p = request.POST
    return render(request, 'backoffice/employee_form.html', {
        'manager':   manager,
        'employee':  employee,
        'mode':      'edit',
        'error':     error,
        'form_data': {
            'employee_id':  p.get('employee_id',  str(employee.employee_id)),
            'name':         p.get('name',         employee.name),
            'name_en':      p.get('name_en',      employee.name_en),
            'department':   p.get('department',   employee.department),
            'role':         p.get('role',         employee.role or ''),
            'access_level': p.get('access_level', str(employee.access_level)),
        },
    })


# ── 직원 삭제 (AJAX) ──────────────────────────────────────────────────────
@login_required
def employee_delete(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)
    try:
        employee = get_object_or_404(Employee, pk=pk)
        name = employee.name
        employee.delete()
        return JsonResponse({'success': True, 'message': f'{name}님이 삭제되었습니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ── FAISS 재학습 (AJAX) ────────────────────────────────────────────────────
@login_required
def retrain_view(request):
    global _retrain_state
    if request.method == 'POST':
        with _retrain_lock:
            if _retrain_state['status'] == 'running':
                return JsonResponse({'ok': False, 'message': '이미 학습이 진행 중입니다.'})
        t = threading.Thread(target=_run_retrain, daemon=True)
        t.start()
        return JsonResponse({'ok': True, 'message': '학습을 시작했습니다.'})

    with _retrain_lock:
        return JsonResponse(dict(_retrain_state))
