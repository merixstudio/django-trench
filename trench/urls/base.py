from django.urls import path

from trench import views


__all__ = [
    "urlpatterns",
]

urlpatterns = [
    path(
        "<str:method>/activate/",
        views.RequestMFAMethodActivationView.as_view(),
        name="mfa-activate",
    ),
    path(
        "<str:method>/activate/confirm/",
        views.RequestMFAMethodActivationConfirmView.as_view(),
        name="mfa-activate-confirm",
    ),
    path(
        "<str:method>/deactivate/",
        views.RequestMFAMethodDeactivationView.as_view(),
        name="mfa-deactivate",
    ),
    path(
        "<str:method>/codes/regenerate/",
        views.RequestMFAMethodBackupCodesRegenerationView.as_view(),
        name="mfa-regenerate-codes",
    ),
    path(
        "code/request/", views.RequestMFAMethodCode.as_view(), name="mfa-request-code"
    ),
    path("mfa/config/", views.GetMFAConfig.as_view(), name="mfa-config-info"),
    path(
        "mfa/user-active-methods/",
        views.ListUserActiveMFAMethods.as_view(),
        name="mfa-list-user-active-methods",
    ),
    path(
        "mfa/change-primary-method/",
        views.ChangePrimaryMethod.as_view(),
        name="mfa-change-primary-method",
    ),
]
