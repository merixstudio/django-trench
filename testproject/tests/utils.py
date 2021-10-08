import pytest
from django.conf import settings

from django.contrib.auth import get_user_model

import jwt
from rest_framework.response import Response
from rest_framework.test import APIClient


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
        algorithms=["HS256"]
    ).get(User.USERNAME_FIELD)
