from django.contrib.auth import get_user_model

from rest_framework.test import APIClient

import jwt
import pytest

header_template ='JWT {}'

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
