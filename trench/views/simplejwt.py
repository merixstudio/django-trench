from django.utils.six import text_type

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from trench.views.base import MFACodeLoginMixin, MFACredentialsLoginMixin


class ObtainJSONWebTokenMixin:
    def handle_user_login(self, request, serializer, *args, **kwargs):
        token = RefreshToken.for_user(serializer.user)
        return Response(
            {
                'refresh': text_type(token),
                'access': text_type(token.access_token)
            }
        )


class JSONWebTokenLoginOrRequestMFACode(MFACredentialsLoginMixin,
                                        ObtainJSONWebTokenMixin,
                                        GenericAPIView):
    pass


class JSONWebTokenLoginWithMFACode(MFACodeLoginMixin,
                                   ObtainJSONWebTokenMixin,
                                   GenericAPIView):
    pass
