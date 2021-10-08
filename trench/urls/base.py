from django.urls import path


__all__ = [
    "urlpatterns",
]

from trench.views import (
    MFAConfigView,
    MFAListActiveUserMethodsView,
    MFAMethodActivationView,
    MFAMethodBackupCodesRegenerationView,
    MFAMethodConfirmActivationView,
    MFAMethodDeactivationView,
    MFAMethodRequestCodeView,
    MFAPrimaryMethodChangeView,
)


urlpatterns = (
    path(
        "<str:method>/activate/",
        MFAMethodActivationView.as_view(),
        name="mfa-activate",
    ),
    path(
        "<str:method>/activate/confirm/",
        MFAMethodConfirmActivationView.as_view(),
        name="mfa-activate-confirm",
    ),
    path(
        "<str:method>/deactivate/",
        MFAMethodDeactivationView.as_view(),
        name="mfa-deactivate",
    ),
    path(
        "<str:method>/codes/regenerate/",
        MFAMethodBackupCodesRegenerationView.as_view(),
        name="mfa-regenerate-codes",
    ),
    path("code/request/", MFAMethodRequestCodeView.as_view(), name="mfa-request-code"),
    path("mfa/config/", MFAConfigView.as_view(), name="mfa-config-info"),
    path(
        "mfa/user-active-methods/",
        MFAListActiveUserMethodsView.as_view(),
        name="mfa-list-user-active-methods",
    ),
    path(
        "mfa/change-primary-method/",
        MFAPrimaryMethodChangeView.as_view(),
        name="mfa-change-primary-method",
    ),
)
