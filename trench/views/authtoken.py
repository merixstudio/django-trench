from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from djoser.views import TokenDestroyView
from djoser import utils
from djoser.conf import settings

from trench.views.base import MFACodeLoginMixin, MFACredentialsLoginMixin


class ObtainAuthTokenMixin:
    def handle_user_login(self, serializer, *args, **kwargs):
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = settings.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data,
            status=status.HTTP_200_OK,
        )


class AuthTokenLoginOrRequestMFACode(MFACredentialsLoginMixin,
                                     ObtainAuthTokenMixin,
                                     GenericAPIView):
    pass


class AuthTokenLoginWithMFACode(MFACodeLoginMixin,
                                ObtainAuthTokenMixin,
                                GenericAPIView):
    pass


AuthTokenLogoutView = TokenDestroyView
