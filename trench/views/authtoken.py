from django.contrib.auth import user_logged_in, user_logged_out

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from trench.serializers import TokenSerializer
from trench.views import MFAFirstStepMixin, MFASecondStepMixin, MFAStepMixin, User


class MFAAuthTokenView(MFAStepMixin):
    def _successful_authentication_response(self, user: User) -> Response:
        token, _ = Token.objects.get_or_create(user=user)
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        return Response(data=TokenSerializer(token).data)


class MFAFirstStepAuthTokenView(MFAAuthTokenView, MFAFirstStepMixin):
    pass


class MFASecondStepAuthTokenView(MFAAuthTokenView, MFASecondStepMixin):
    pass


class MFALogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request) -> Response:
        Token.objects.filter(user=request.user).delete()
        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
