from django.conf import settings
from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from trench.views import authtoken as views


__all__ = [
    'urlpatterns',
]

if 'djoser' not in settings.INSTALLED_APPS:
    msg = _(
        'Djoser not found in INSTALLED_APPS. '
        'Make sure you\'ve installed it, and '
        'add appropriate entry in settings.'
    )
    raise ImproperlyConfigured(msg)

urlpatterns = [
    url(
        r'^login/$',
        views.AuthTokenLoginOrRequestMFACode.as_view(),
        name='mfa-authtoken-login',
    ),
    url(
        r'^login/code/',
        views.AuthTokenLoginWithMFACode.as_view(),
        name='mfa-authtoken-login-code',
    ),
    url(
        r'^logout/',
        views.AuthTokenLogoutView.as_view(),
        name='authtoken-logout',
    )
]
