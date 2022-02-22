from django.conf import settings
from django.contrib.auth import get_user_model

import jwt
from django.contrib.auth.models import AbstractUser
from rest_framework.response import Response
from rest_framework.test import APIClient
from typing import Optional

from trench.backends.base import AbstractMessageDispatcher
from trench.backends.provider import get_mfa_handler
from trench.models import MFAMethod


User = get_user_model()


class TrenchAPIClient(APIClient):
    _HEADER_TEMPLATE = "Bearer {}"
    _DEFAULT_TOKEN_FIELD = "access"
    PATH_AUTH_JWT_LOGIN = "/auth/jwt/login/"
    PATH_AUTH_JWT_LOGIN_CODE = "/auth/jwt/login/code/"
    PATH_AUTH_TOKEN_LOGIN = "/auth/token/login/"
    PATH_AUTH_TOKEN_LOGIN_CODE = "/auth/token/login/code/"

    def authenticate(self, user: AbstractUser, path: str = PATH_AUTH_JWT_LOGIN) -> Response:
        response = self._first_factor_request(user=user, path=path)
        self._update_jwt_from_response(response)
        return response

    def authenticate_multi_factor(
        self,
        mfa_method: MFAMethod,
        user: AbstractUser,
        path: str = PATH_AUTH_JWT_LOGIN,
        path_2nd_factor: str = PATH_AUTH_JWT_LOGIN_CODE,
    ) -> Response:
        response = self._first_factor_request(user=user, path=path)
        ephemeral_token = self._extract_ephemeral_token_from_response(response=response)
        handler = get_mfa_handler(mfa_method=mfa_method)
        response = self._second_factor_request(
            handler=handler, ephemeral_token=ephemeral_token, path=path_2nd_factor
        )
        self._update_jwt_from_response(response=response)
        return response

    def _first_factor_request(
        self, user: AbstractUser, path: str = PATH_AUTH_JWT_LOGIN
    ) -> Response:
        return self.post(
            path=path,
            data={
                "username": getattr(user, User.USERNAME_FIELD),
                "password": "secretkey",
            },
            format="json",
        )

    def _second_factor_request(
        self,
        ephemeral_token: str,
        handler: Optional[AbstractMessageDispatcher] = None,
        code: Optional[str] = None,
        path: str = PATH_AUTH_JWT_LOGIN_CODE,
    ) -> Response:
        if handler is None and code is None:
            raise ValueError("handler and code can't be None simultaneously")
        return self.post(
            path=path,
            data={
                "ephemeral_token": ephemeral_token,
                "code": handler.create_code() if code is None else code,
            },
            format="json",
        )

    def _update_jwt_from_response(self, response: Response):
        jwt = self._get_token_from_response(response)
        self.credentials(HTTP_AUTHORIZATION=self._HEADER_TEMPLATE.format(jwt))

    def _extract_ephemeral_token_from_response(self, response: Response) -> str:
        return response.data.get("ephemeral_token")

    @classmethod
    def _get_token_from_response(
        cls, response: Response, token_field: str = _DEFAULT_TOKEN_FIELD
    ) -> str:
        return response.data.get(token_field)

    @classmethod
    def get_username_from_jwt(
        cls, response: Response, token_field: str = _DEFAULT_TOKEN_FIELD
    ) -> Optional[str]:
        return jwt.decode(
            response.data.get(token_field),
            key=settings.SECRET_KEY,
            verify=False,
            algorithms=["HS256"],
        ).get(User.USERNAME_FIELD)
