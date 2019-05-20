from django.conf.urls import url

from trench import views
from trench.settings import api_settings


__all__ = [
    'urlpatterns',
]

mfa_methods_choices = '|'.join(api_settings.MFA_METHODS.keys())

urlpatterns = [
    url(
        r'^(?P<method>({}))/activate/$'.format(mfa_methods_choices),
        views.RequestMFAMethodActivationView.as_view(),
        name='mfa-activate',
    ),
    url(
        r'^(?P<method>({}))/activate/confirm/$'.format(mfa_methods_choices),
        views.RequestMFAMethodActivationConfirmView.as_view(),
        name='mfa-activate-confirm',
    ),
    url(
        r'^(?P<method>({}))/deactivate/$'.format(mfa_methods_choices),
        views.RequestMFAMethodDeactivationView.as_view(),
        name='mfa-deactivate',
    ),
    url(
        r'^(?P<method>({}))/codes/regenerate/$'.format(mfa_methods_choices),
        views.RequestMFAMethodBackupCodesRegenerationView.as_view(),
        name='mfa-regenerate-codes',
    ),
    url(
        r'^code/request/$',
        views.RequestMFAMethodCode.as_view(),
        name='mfa-request-code',
    ),
    url(
        r'^mfa/config/$',
        views.GetMFAConfig.as_view(),
        name='mfa-config-info',
    ),
    url(
        r'^mfa/user-active-methods/$',
        views.ListUserActiveMFAMethods.as_view(),
        name='mfa-list-user-active-methods',
    ),
    url(
        r'^mfa/change-primary-method/$',
        views.ChangePrimaryMethod.as_view(),
        name='mfa-change-primary-method',
    ),
]
