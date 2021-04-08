from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import re_path
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
    re_path(
        r"^login/$",
        views.AuthTokenLoginOrRequestMFACode.as_view(),
        name="mfa-authtoken-login",
    ),
    re_path(
        r"^login/code/",
        views.AuthTokenLoginWithMFACode.as_view(),
        name="mfa-authtoken-login-code",
    ),
    re_path(
        r"^logout/",
        views.AuthTokenLogoutView.as_view(),
        name="authtoken-logout",
    ),
]
