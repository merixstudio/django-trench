import pytest

from django.contrib.auth import get_user_model

import jwt
from rest_framework.test import APIClient


User = get_user_model()

header_template = 'JWT {}'
token_field = 'token'

# For simpleJWT
# header_template ='Bearer {}'
# token_field = 'access'

def get_token_from_response(response):
    return response.data.get(token_field)

@pytest.mark.django_db
def login(user):
    client = APIClient()
    return client.post(
        path='/auth/login/',
        data={
            'username': getattr(
                user,
                User.USERNAME_FIELD,
            ),
            'password': 'secretkey',
        },
        format='json',
    )


def get_username_from_jwt(response):
    return jwt.decode(
        response.data.get(token_field),
        verify=False,
    ).get(User.USERNAME_FIELD)
