from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import LoginLog


def _get_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    LoginLog.objects.create(
        user=user,
        username=user.username,
        email=user.email,
        action=LoginLog.ACTION_LOGIN,
        client_ip=_get_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        is_admin=user.is_staff or user.is_superuser,
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if not user:
        return
    LoginLog.objects.create(
        user=user,
        username=user.username,
        email=user.email,
        action=LoginLog.ACTION_LOGOUT,
        client_ip=_get_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        is_admin=user.is_staff or user.is_superuser,
    )
