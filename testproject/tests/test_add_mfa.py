import pytest

from django.contrib.auth import get_user_model

from rest_framework.status import HTTP_200_OK

from tests.utils import TrenchAPIClient
from trench.command.create_otp import create_otp_command
from trench.command.create_secret import create_secret_command
from trench.settings import MfaMethods


User = get_user_model()


@pytest.mark.django_db
def test_add_user_mfa(active_user):
    client = TrenchAPIClient()
    client.authenticate(user=active_user)
    secret = create_secret_command()
    response = client.post(
        path=f"/auth/{MfaMethods.EMAIL}/activate/",
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
    mfa_method = active_user.mfa_methods.filter(is_primary=True).first()
    client = TrenchAPIClient()
    client.authenticate_multi_factor(mfa_method=mfa_method, user=active_user)
    response = client.get(path="/auth/mfa/user-active-methods/")
    assert len(response.data) == 4
