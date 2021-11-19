import pytest

from django.contrib.auth import get_user_model
from rest_framework.status import HTTP_200_OK

from rest_framework.test import APIClient

from tests.utils import (
    PATH_AUTH_JWT_LOGIN_CODE,
    get_token_from_response,
    header_template,
    login,
)
from trench.backends.provider import get_mfa_handler
from trench.command.create_otp import create_otp_command
from trench.command.create_secret import create_secret_command


User = get_user_model()


@pytest.mark.django_db
def test_add_user_mfa(active_user):
    client = APIClient()
    login_response = login(active_user)
    token = get_token_from_response(login_response)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    secret = create_secret_command()
    response = client.post(
        path="/auth/email/activate/",
        data={
            "secret": secret,
            "code": create_otp_command(secret=secret).now(),
            "user": getattr(active_user, active_user.USERNAME_FIELD),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_user_with_many_methods(active_user_with_many_otp_methods):
    client = APIClient()
    active_user, _ = active_user_with_many_otp_methods
    initial_active_methods_count = active_user.mfa_methods.filter(
        is_active=True
    ).count()
    first_step = login(active_user)
    assert first_step.status_code == HTTP_200_OK

    primary_method = active_user.mfa_methods.filter(is_primary=True).first()
    # As user has several methods get first and get sure only 1 is primary
    assert primary_method is not None

    handler = get_mfa_handler(mfa_method=primary_method)
    second_step_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    # Log in the user in the second step and make sure it is correct
    assert second_step_response.status_code == HTTP_200_OK

    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(second_step_response)
        )
    )
    active_methods_response = client.get(
        path="/auth/mfa/user-active-methods/",
    )

    # This user should have 3 methods, so we check that return has 3 methods
    assert len(active_methods_response.data) == initial_active_methods_count
