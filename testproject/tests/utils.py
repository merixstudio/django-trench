from typing import Optional, Tuple

import pytest

from django.conf import settings
from django.contrib.auth import get_user_model

import jwt
from rest_framework.response import Response
from rest_framework.test import APIClient

from trench.backends.base import AbstractMessageDispatcher
from trench.backends.provider import get_mfa_handler

User = get_user_model()

header_template = "Bearer {}"
default_token_field = "access"


def get_token_from_response(response: Response, token_field=default_token_field):
    return response.data.get(token_field)


PATH_AUTH_JWT_LOGIN = "/auth/jwt/login/"
PATH_AUTH_JWT_LOGIN_CODE = "/auth/jwt/login/code/"


@pytest.mark.django_db
def login(user, path=PATH_AUTH_JWT_LOGIN) -> Response:
    return APIClient().post(
        path=path,
        data={
            "username": getattr(user, User.USERNAME_FIELD),
            "password": "secretkey",
        },
        format="json",
    )


def get_username_from_jwt(response, token_field=default_token_field):
    return jwt.decode(
        response.data.get(token_field),
        key=settings.SECRET_KEY,
        verify=False,
        algorithms=["HS256"],
    ).get(User.USERNAME_FIELD)


def get_authenticated_api_client_and_mfa_handler(user, primary_method: Optional[bool] = None) -> Tuple[APIClient, AbstractMessageDispatcher]:
    client = APIClient()
    first_step = login(user)
    mfa_methods_qs = user.mfa_methods
    if primary_method is not None:
        mfa_methods_qs = mfa_methods_qs.filter(is_primary=primary_method)
    mfa_method = mfa_methods_qs.first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    jwt = get_token_from_response(response)
    client.credentials(HTTP_AUTHORIZATION=header_template.format(jwt))
    return client, handler
