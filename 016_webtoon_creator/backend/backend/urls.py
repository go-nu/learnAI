from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
import api.views as api_views


urlpatterns = [
    # ── 관리자 (Django Admin) ──────────────────────────────
    path("admin/", admin.site.urls),

    # ── 관리자 HTML 페이지 ─────────────────────────────────
    path("",         views.index,          name="index"),
    path("login",    views.login_view,     name="login"),
    path("logout",   views.logout_view,    name="logout"),
    path("dashboard",views.dashboard_view, name="dashboard"),

    # ── Google OAuth2 (social-auth-app-django) ─────────────
    # /auth/login/google-oauth2/  → Google로 리다이렉트
    # /auth/complete/google-oauth2/ → 콜백 처리
    path("auth/", include("social_django.urls", namespace="social")),

    # ── REST API ───────────────────────────────────────────
    path("api/auth/csrf/",     api_views.CSRFView.as_view()),
    path("api/auth/me/",       api_views.MeView.as_view()),
    path("api/auth/login/",    api_views.LoginView.as_view()),
    path("api/auth/register/", api_views.RegisterView.as_view()),
    path("api/auth/logout/",   api_views.LogoutView.as_view()),

    # ── 웹툰 CRUD ──────────────────────────────────────────
    path("api/webtoons/",          api_views.WebtoonListView.as_view()),
    path("api/webtoons/<int:pk>/", api_views.WebtoonDetailView.as_view()),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
