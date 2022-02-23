import pytest

from rest_framework.status import HTTP_200_OK

from tests.utils import TrenchAPIClient
from trench.utils import user_token_generator


@pytest.mark.django_db(transaction=True)
def test_auth_token_first_step(active_user_with_email_otp):
    client = TrenchAPIClient()
    response = client.authenticate(
        user=active_user_with_email_otp, path=client.PATH_AUTH_TOKEN_LOGIN
    )

    assert response.status_code == HTTP_200_OK
    assert (
        user_token_generator.check_token(
            user=None, token=client._extract_ephemeral_token_from_response(response)
        )
        == active_user_with_email_otp
    )


@pytest.mark.django_db(transaction=True)
def test_auth_token_both_steps(active_user_with_email_otp):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    response = client.authenticate_multi_factor(
        user=active_user_with_email_otp,
        mfa_method=mfa_method,
        path=client.PATH_AUTH_TOKEN_LOGIN,
        path_2nd_factor=client.PATH_AUTH_TOKEN_LOGIN_CODE,
    )
    assert response.status_code == HTTP_200_OK
    assert response.data.get("auth_token") is not None
