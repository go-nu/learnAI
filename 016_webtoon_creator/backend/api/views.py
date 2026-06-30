"""
ToonCraft API 뷰
- 인증 관련: 로그인, 회원가입, 내 정보, 로그아웃, CSRF
"""

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import User, Webtoon


# ── CSRF 토큰 발급 ─────────────────────────────────────────
class CSRFView(APIView):
    """GET /api/auth/csrf/ — csrftoken 쿠키 발급"""
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"success": True, "csrfToken": get_token(request)})


# ── 내 정보 조회 / 수정 ────────────────────────────────────
class MeView(APIView):
    """GET /api/auth/me/ — 로그인 여부 확인 및 사용자 정보 반환
       PATCH /api/auth/me/ — 닉네임·이메일·비밀번호 수정"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "success": True,
            "data": {
                "id":       user.id,
                "username": user.username,
                "email":    user.email,
                "nickname": user.nickname or user.username,
            },
        })

    def patch(self, request):
        user     = request.user
        nickname = request.data.get("nickname", "").strip()
        email    = request.data.get("email", "").strip()
        password = request.data.get("password", "").strip()

        if email and email != user.email:
            from .models import User as UserModel
            if UserModel.objects.filter(email=email).exclude(pk=user.pk).exists():
                return Response(
                    {"success": False, "message": "이미 사용 중인 이메일입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email = email

        if nickname:
            user.nickname = nickname

        if password:
            if len(password) < 8:
                return Response(
                    {"success": False, "message": "비밀번호는 8자 이상이어야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(password)
            # 비밀번호 변경 후 세션 갱신
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        user.save()
        return Response({
            "success": True,
            "message": "회원정보가 수정되었습니다.",
            "data": {
                "id":       user.id,
                "username": user.username,
                "email":    user.email,
                "nickname": user.nickname or user.username,
            },
        })


# ── 로그인 ─────────────────────────────────────────────────
class LoginView(APIView):
    """POST /api/auth/login/ — 아이디/비밀번호 로그인"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "").strip()

        if not username or not password:
            return Response(
                {"success": False, "message": "아이디와 비밀번호를 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # AUTHENTICATION_BACKENDS 가 여러 개일 때 backend 명시 필요
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return Response({
            "success": True,
            "message": "로그인에 성공했습니다.",
            "data": {
                "id":       user.id,
                "username": user.username,
                "email":    user.email,
                "nickname": user.nickname or user.username,
            },
        })


# ── 회원가입 ───────────────────────────────────────────────
class RegisterView(APIView):
    """POST /api/auth/register/ — 이메일/아이디/비밀번호 회원가입"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "").strip()
        email    = request.data.get("email", "").strip()
        password = request.data.get("password", "").strip()
        nickname = request.data.get("nickname", "").strip()

        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[Register] username={username!r} email={email!r} data_keys={list(request.data.keys())}")

        # 필수 입력값 검사
        if not username or not email or not password:
            return Response(
                {"success": False, "message": "아이디, 이메일, 비밀번호는 필수 입력값입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 중복 검사
        if User.objects.filter(username=username).exists():
            logger.warning(f"[Register] Duplicate username: {username!r}")
            return Response(
                {"success": False, "message": "이미 사용 중인 아이디입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email=email).exists():
            logger.warning(f"[Register] Duplicate email: {email!r}")
            return Response(
                {"success": False, "message": "이미 사용 중인 이메일입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 비밀번호 최소 길이 검사
        if len(password) < 8:
            return Response(
                {"success": False, "message": "비밀번호는 8자 이상이어야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create_user + login 을 하나의 트랜잭션으로 묶어 로그인 실패 시 유저 생성도 롤백
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                nickname=nickname or username,
            )
            # AUTHENTICATION_BACKENDS 가 여러 개일 때 backend 명시 필요
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return Response(
            {
                "success": True,
                "message": "회원가입이 완료되었습니다.",
                "data": {
                    "id":       user.id,
                    "username": user.username,
                    "email":    user.email,
                    "nickname": user.nickname,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# ── 로그아웃 ───────────────────────────────────────────────
class LogoutView(APIView):
    """POST /api/auth/logout/ — 세션 종료"""

    def post(self, request):
        logout(request)
        return Response({"success": True, "message": "로그아웃 되었습니다."})


# ── 웹툰 목록 조회 / 생성 ───────────────────────────────────
class WebtoonListView(APIView):
    """
    GET  /api/webtoons/ — 목록 조회 (페이징·검색)
    POST /api/webtoons/ — 웹툰 생성 (multipart/form-data)
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _serialize(w, request):
        return {
            'id':          w.id,
            'title':       w.title,
            'genre':       w.genre,
            'status':      w.status,
            'description': w.description,
            'cover_image': request.build_absolute_uri(w.cover_image.url) if w.cover_image else None,
            'created_at':  w.created_at.strftime('%Y-%m-%d'),
        }

    def get(self, request):
        qs = Webtoon.objects.filter(author=request.user).order_by('-created_at')

        # 검색
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(title__icontains=search)

        # 페이지네이션
        try:
            page      = max(1, int(request.query_params.get('page', 1)))
            page_size = max(1, min(50, int(request.query_params.get('page_size', 10))))
        except (ValueError, TypeError):
            page, page_size = 1, 10

        total    = qs.count()
        start    = (page - 1) * page_size
        webtoons = qs[start:start + page_size]

        return Response({
            'success': True,
            'data': {
                'webtoons':    [self._serialize(w, request) for w in webtoons],
                'total':       total,
                'page':        page,
                'page_size':   page_size,
                'total_pages': max(1, (total + page_size - 1) // page_size),
            },
        })

    def post(self, request):
        title       = request.data.get('title', '').strip()
        genre       = request.data.get('genre', 'etc').strip()
        description = request.data.get('description', '').strip()
        status_val  = request.data.get('status', 'draft').strip()
        cover_image = request.FILES.get('cover_image')

        if not title:
            return Response(
                {'success': False, 'message': '제목을 입력해 주세요.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        webtoon = Webtoon.objects.create(
            author=request.user,
            title=title,
            genre=genre,
            description=description,
            status=status_val,
            cover_image=cover_image,
        )
        return Response({
            'success': True,
            'message': '웹툰이 등록되었습니다.',
            'data': self._serialize(webtoon, request),
        }, status=status.HTTP_201_CREATED)


# ── 웹툰 단건 조회 / 수정 / 삭제 ──────────────────────────────
class WebtoonDetailView(APIView):
    """
    GET    /api/webtoons/{pk}/ — 단건 조회
    PATCH  /api/webtoons/{pk}/ — 수정
    DELETE /api/webtoons/{pk}/ — 삭제
    """
    permission_classes = [IsAuthenticated]

    def _get_webtoon(self, pk, user):
        try:
            return Webtoon.objects.get(pk=pk, author=user)
        except Webtoon.DoesNotExist:
            return None

    @staticmethod
    def _serialize(w, request):
        return {
            'id':          w.id,
            'title':       w.title,
            'genre':       w.genre,
            'status':      w.status,
            'description': w.description,
            'cover_image': request.build_absolute_uri(w.cover_image.url) if w.cover_image else None,
            'created_at':  w.created_at.strftime('%Y-%m-%d'),
        }

    def get(self, request, pk):
        webtoon = self._get_webtoon(pk, request.user)
        if not webtoon:
            return Response(
                {'success': False, 'message': '웹툰을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'success': True, 'data': self._serialize(webtoon, request)})

    def patch(self, request, pk):
        webtoon = self._get_webtoon(pk, request.user)
        if not webtoon:
            return Response(
                {'success': False, 'message': '웹툰을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if 'title' in request.data:
            title = request.data.get('title', '').strip()
            if not title:
                return Response(
                    {'success': False, 'message': '제목을 입력해 주세요.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            webtoon.title = title
        if 'genre' in request.data:
            webtoon.genre = request.data.get('genre', 'etc')
        if 'description' in request.data:
            webtoon.description = request.data.get('description', '')
        if 'status' in request.data:
            webtoon.status = request.data.get('status', 'draft')
        if 'cover_image' in request.FILES:
            webtoon.cover_image = request.FILES['cover_image']

        webtoon.save()
        return Response({
            'success': True,
            'message': '웹툰이 수정되었습니다.',
            'data': self._serialize(webtoon, request),
        })

    def delete(self, request, pk):
        webtoon = self._get_webtoon(pk, request.user)
        if not webtoon:
            return Response(
                {'success': False, 'message': '웹툰을 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        webtoon.delete()
        return Response({'success': True, 'message': '웹툰이 삭제되었습니다.'})
