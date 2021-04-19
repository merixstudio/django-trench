import pytest

from django.contrib.auth import get_user_model

import jwt
from rest_framework.response import Response
from rest_framework.test import APIClient


User = get_user_model()

header_template = 'Bearer {}'
default_token_field = 'access'


def get_token_from_response(response: Response, token_field=default_token_field):
    return response.data.get(token_field)


@pytest.mark.django_db
def login(user, path='/auth/login/') -> Response:
    payload = {
        'username': getattr(user, User.USERNAME_FIELD),
        'password': 'secretkey',
    }
    client = APIClient()
    return client.post(
        path=path,
        data=payload,
        format='json',
    )


def get_username_from_jwt(response, token_field=default_token_field):
    return jwt.decode(
        response.data.get(token_field),
        verify=False,
    ).get(User.USERNAME_FIELD)
