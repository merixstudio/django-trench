from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import path
from django.utils.translation import gettext_lazy as _

from trench.views import authtoken as views


__all__ = [
    "urlpatterns",
]

if "djoser" not in settings.INSTALLED_APPS:
    msg = _(
        "Djoser not found in INSTALLED_APPS. "
        "Make sure you've installed it, and "
        "add appropriate entry in settings."
    )
    raise ImproperlyConfigured(msg)

urlpatterns = [
    path(
        "login/",
        views.AuthTokenLoginOrRequestMFACode.as_view(),
        name="mfa-authtoken-login",
    ),
    path(
        "login/code/",
        views.AuthTokenLoginWithMFACode.as_view(),
        name="mfa-authtoken-login-code",
    ),
    path(
        "logout/",
        views.AuthTokenLogoutView.as_view(),
        name="authtoken-logout",
    ),
]
