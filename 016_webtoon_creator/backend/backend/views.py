from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


# 루트 진입점
def index(request):
    return HttpResponse("안녕하세요")


# 관리자 로그인
def login_view(request):
    # 이미 로그인된 경우 대시보드로 이동
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        else:
            error = '아이디 또는 비밀번호가 올바르지 않습니다.'

    return render(request, 'admin/login.html', {'error': error})


# 관리자 로그아웃
def logout_view(request):
    logout(request)
    return redirect('login')


# 관리자 대시보드 (로그인 필수)
@login_required(login_url='/login')
def dashboard_view(request):
    return render(request, 'admin/dashboard.html')
