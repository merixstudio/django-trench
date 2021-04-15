from trench.views.base import (
    MFAFirstStepJWTView,
    MFALogoutView,
    MFASecondStepAuthTokenView,
    MFASecondStepJWTView,
)


class AuthTokenLoginOrRequestMFACode(MFAFirstStepJWTView, MFASecondStepAuthTokenView):
    # TODO - this is currently not used - do we want to have it anyway?
    pass


class AuthTokenLoginWithMFACode(MFASecondStepJWTView, MFASecondStepAuthTokenView):
    # TODO - this is currently not used - do we want to have it anyway?
    pass


AuthTokenLogoutView = MFALogoutView
