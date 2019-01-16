from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework_jwt.utils import (
    jwt_encode_handler,
    jwt_payload_handler,
    jwt_response_payload_handler,
)

from trench.views.base import MFACodeLoginMixin, MFACredentialsLoginMixin


class ObtainJSONWebTokenMixin:
    def handle_user_login(self, request, serializer, *args, **kwargs):
        token = jwt_encode_handler(jwt_payload_handler(serializer.user))
        return Response(
            jwt_response_payload_handler(token, serializer.user, request)
        )


class JSONWebTokenLoginOrRequestMFACode(MFACredentialsLoginMixin,
                                        ObtainJSONWebTokenMixin,
                                        GenericAPIView):
    pass


class JSONWebTokenLoginWithMFACode(MFACodeLoginMixin,
                                   ObtainJSONWebTokenMixin,
                                   GenericAPIView):
    pass
