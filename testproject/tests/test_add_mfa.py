import pytest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from flaky import flaky
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from tests.utils import TrenchAPIClient
from trench.command.create_otp import create_otp_command
from trench.command.create_secret import create_secret_command


User: AbstractUser = get_user_model()


@pytest.mark.django_db
def test_add_user_mfa(active_user):
    client = TrenchAPIClient()
    client.authenticate(user=active_user)
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
def test_should_fail_on_add_user_mfa_with_invalid_source_field(active_user: User):
    client = TrenchAPIClient()
    client.authenticate(user=active_user)
    secret = create_secret_command()
    settings.TRENCH_AUTH["MFA_METHODS"]["email"]["SOURCE_FIELD"] = "email_test"

    response = client.post(
        path="/auth/email/activate/",
        data={
            "secret": secret,
            "code": create_otp_command(secret=secret, interval=60).now(),
            "user": getattr(active_user, active_user.USERNAME_FIELD),
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response.data.get("error")
        == "Field name `email_test` is not valid for model `User`."
    )
    settings.TRENCH_AUTH["MFA_METHODS"]["email"]["SOURCE_FIELD"] = "email"


@flaky
@pytest.mark.django_db
def test_user_with_many_methods(active_user_with_many_otp_methods):
    active_user, _ = active_user_with_many_otp_methods
    mfa_method = active_user.mfa_methods.filter(is_primary=True).first()
    client = TrenchAPIClient()
    client.authenticate_multi_factor(mfa_method=mfa_method, user=active_user)
    response = client.get(path="/auth/mfa/user-active-methods/")
    assert len(response.data) == 4
