from trench.views.base import MFACodeLoginMixin, MFACredentialsLoginMixin


class JSONWebTokenLoginOrRequestMFACode(MFACredentialsLoginMixin):
    pass


class JSONWebTokenLoginWithMFACode(MFACodeLoginMixin):
    pass
