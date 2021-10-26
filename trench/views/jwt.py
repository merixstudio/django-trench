from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from trench.views import MFAFirstStepMixin, MFASecondStepMixin, MFAStepMixin, User


class MFAJWTView(MFAStepMixin):
    def _successful_authentication_response(self, user: User) -> Response:
        token = RefreshToken.for_user(user=user)
        return Response(data={"refresh": str(token), "access": str(token.access_token)})


class MFAFirstStepJWTView(MFAJWTView, MFAFirstStepMixin):
    pass


class MFASecondStepJWTView(MFAJWTView, MFASecondStepMixin):
    pass
