import pytest

from django.contrib.auth import get_user_model

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from tests.utils import (
    PATH_AUTH_JWT_LOGIN_CODE,
    get_token_from_response,
    header_template,
    login,
    get_authenticated_api_client_and_mfa_handler,
)

from trench.command.create_otp import create_otp_command
from trench.command.create_secret import create_secret_command


User = get_user_model()


@pytest.mark.django_db
def test_add_user_mfa(active_user):
    client = APIClient()
    login_response = login(active_user)
    token = get_token_from_response(login_response)
    client.credentials(HTTP_AUTHORIZATION=header_template.format(token))
    secret = create_secret_command()
    response = client.post(
        path="/auth/email/activate/",
        data={
            "secret": secret,
            "code": create_otp_command(secret=secret, interval=60).now(),
            "user": getattr(active_user, active_user.USERNAME_FIELD),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_user_with_many_methods(active_user_with_many_otp_methods):
    active_user, _ = active_user_with_many_otp_methods
    client, handler = get_authenticated_api_client_and_mfa_handler(
        active_user, primary_method=True
    )
    active_methods_response = client.get(
        path="/auth/mfa/user-active-methods/"
    )
    assert len(active_methods_response.data) == 4
