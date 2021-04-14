from trench.views.base import (
    MFACodeLoginMixin,
    MFACredentialsLoginMixin,
    MFALoginView,
    MFALogoutView,
)


class AuthTokenLoginOrRequestMFACode(MFACredentialsLoginMixin, MFALoginView):
    # TODO - this is currently not used - do we want to have it anyway?
    pass


class AuthTokenLoginWithMFACode(MFACodeLoginMixin, MFALoginView):
    # TODO - this is currently not used - do we want to have it anyway?
    pass


AuthTokenLogoutView = MFALogoutView
