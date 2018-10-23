import pytest
import jwt
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


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
        response.data.get('token'),
        verify=False,
    ).get(User.USERNAME_FIELD)
