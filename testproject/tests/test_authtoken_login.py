import pytest
from rest_framework.status import HTTP_200_OK

from rest_framework.test import APIClient

from tests.utils import login
from trench.backends.provider import get_mfa_handler
from trench.utils import user_token_generator


@pytest.mark.django_db
def test_authtoken_both_steps(active_user_with_email_otp):
    # first step
    first_step_response = login(active_user_with_email_otp, path="/auth/token/login/")
    assert first_step_response.status_code == HTTP_200_OK
    assert (
        user_token_generator.check_token(
            user=None, token=first_step_response.data.get("ephemeral_token")
        )
        == active_user_with_email_otp
    )
    # second step
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    second_step_response = APIClient().post(
        path="/auth/token/login/code/",
        data={
            "ephemeral_token": first_step_response.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    assert second_step_response.status_code == HTTP_200_OK
    assert second_step_response.data.get("auth_token") is not None
