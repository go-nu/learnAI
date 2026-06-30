"""
Django settings for ToonCraft 프로젝트
"""

from pathlib import Path

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# 보안 키 (운영 환경에서는 환경변수로 관리)
SECRET_KEY = "django-insecure-7!h&#id13#l_%(zj&$)2g@#9um61c35*lue3y*_c4(4y4+^c=="

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "tooncraft.co.kr"]

# 설치된 앱
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 서드파티
    "rest_framework",
    "corsheaders",
    "social_django",
    # 프로젝트 앱
    "api",
]

# 커스텀 사용자 모델
AUTH_USER_MODEL = "api.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",           # CORS — 반드시 최상단
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
]

ROOT_URLCONF = "backend.urls"

# 템플릿 설정 — /templates 디렉토리 등록
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# 데이터베이스 — MariaDB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "tooncraftdb",
        "USER": "tooncraft",
        "PASSWORD": "1234",
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# 비밀번호 유효성 검사
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 국제화
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# 정적 파일
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

# 미디어 파일 (업로드 이미지)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 기본 기본키 타입
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Django REST Framework ──────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}

# ── CORS (프론트엔드 localhost:3000 허용) ──────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True          # withCredentials 쿠키 허용
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ── 세션/CSRF 쿠키 설정 ────────────────────────────────────
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE   = False        # 개발환경 HTTP 허용
CSRF_COOKIE_SAMESITE    = "Lax"
CSRF_COOKIE_HTTPONLY    = False        # JS에서 읽을 수 있어야 함

# ── Social Auth — Google OAuth2 ────────────────────────────
AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]

# Google Cloud Console에서 발급한 키를 .env 또는 여기에 설정
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY    = ""   # Client ID
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ""   # Client Secret

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# 로그인 성공 후 프론트엔드로 리다이렉트
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "http://localhost:3000/dashboard"
LOGIN_REDIRECT_URL             = "http://localhost:3000/dashboard"
LOGIN_URL                      = "http://localhost:3000/login"

# social_django 파이프라인 — 커스텀 User 모델과 호환
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

# social_django context processors
TEMPLATES[0]["OPTIONS"]["context_processors"] += [
    "social_django.context_processors.backends",
    "social_django.context_processors.login_redirect",
]

# 개발용 로그 — api 앱의 WARNING 이상을 콘솔에 출력
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "api": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
