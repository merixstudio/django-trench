import pytest

from django.contrib.auth import get_user_model

from trench.backends.sms_api import SMSAPIMessageDispatcher


User = get_user_model()


@pytest.mark.django_db
def test_smsapi_backend_without_credentials(
    active_user_with_sms_otp,
    settings,
):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name="sms_twilio")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]
    response = SMSAPIMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details") == "Credentials are required."


@pytest.mark.django_db
def test_smsapi_backend_with_wrong_credentials(
    active_user_with_sms_otp,
    settings,
):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name="sms_twilio")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]
    settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"][
        "SMSAPI_ACCESS_TOKEN"
    ] = "wrong-token"
    response = SMSAPIMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert "Authorization failed" == response.data.get("details")
