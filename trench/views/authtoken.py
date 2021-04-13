from rest_framework.generics import GenericAPIView

from trench.views.base import (
    MFACodeLoginMixin,
    MFACredentialsLoginMixin,
    MFALoginView,
    MFALogoutView,
)


class AuthTokenLoginOrRequestMFACode(
    MFACredentialsLoginMixin, MFALoginView, GenericAPIView
):
    pass


class AuthTokenLoginWithMFACode(MFACodeLoginMixin, MFALoginView, GenericAPIView):
    pass


AuthTokenLogoutView = MFALogoutView
