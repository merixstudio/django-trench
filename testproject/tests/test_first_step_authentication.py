import pytest

from django.contrib.auth import get_user_model

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from tests.utils import TrenchAPIClient
from trench.utils import user_token_generator


User = get_user_model()


@pytest.mark.django_db(transaction=True)
def test_get_ephemeral_token(active_user_with_email_otp):
    client = TrenchAPIClient()
    response = client.authenticate(user=active_user_with_email_otp)
    assert response.status_code == HTTP_200_OK
    assert (
        user_token_generator.check_token(
            user=None,
            token=client._extract_ephemeral_token_from_response(response=response),
        )
        == active_user_with_email_otp
    )


@pytest.mark.django_db(transaction=True)
def test_deactivated_user(deactivated_user_with_email_otp):
    client = TrenchAPIClient()
    response = client.authenticate(user=deactivated_user_with_email_otp)
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db(transaction=True)
def test_get_jwt_without_otp(active_user):
    client = TrenchAPIClient()
    response = client.authenticate(user=active_user)
    assert response.status_code == HTTP_200_OK
    assert client.get_username_from_jwt(response=response) == getattr(
        active_user,
        User.USERNAME_FIELD,
    )


@pytest.mark.django_db(transaction=True)
def test_login_disabled_user(inactive_user):
    client = TrenchAPIClient()
    response = client.authenticate(user=inactive_user)
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        "Unable to login with provided credentials."
        or "User account is disabled." in response.data.get("non_field_errors")
    )


@pytest.mark.django_db(transaction=True)
def test_login_missing_field(active_user):
    client = TrenchAPIClient()
    response = client.post(
        path=client.PATH_AUTH_JWT_LOGIN,
        data={
            "username": "",
            "password": "secretkey",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert "This field may not be blank." in response.data.get(User.USERNAME_FIELD)


@pytest.mark.django_db(transaction=True)
def test_login_wrong_password(active_user):
    client = TrenchAPIClient()
    response = client.post(
        path=client.PATH_AUTH_JWT_LOGIN,
        data={
            "username": getattr(
                active_user,
                User.USERNAME_FIELD,
            ),
            "password": "wrong",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("error") == "Unable to login with provided credentials."
