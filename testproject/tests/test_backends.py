import pytest

from django.contrib.auth import get_user_model

from trench.backends.application import ApplicationMessageDispatcher
from trench.backends.sms_api import SMSAPIMessageDispatcher
from trench.exceptions import MissingConfigurationError

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


@pytest.mark.django_db
def test_sms_backend_misconfiguration_error(active_user_with_sms_otp, settings):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name="sms_twilio")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]
    current_source = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]["SOURCE_FIELD"]
    settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]["SOURCE_FIELD"] = "invalid.source"
    with pytest.raises(MissingConfigurationError):
        SMSAPIMessageDispatcher(mfa_method=auth_method, config=conf).dispatch_message()
    settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]["SOURCE_FIELD"] = current_source


@pytest.mark.django_db
def test_application_backend_generating_url_successfully(active_user_with_application_otp, settings):
    auth_method = active_user_with_application_otp.mfa_methods.get(name="app")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["app"]
    response = ApplicationMessageDispatcher(mfa_method=auth_method, config=conf).dispatch_message()
    assert response.data.get("details")[:44] == "otpauth://totp/MyApplication:imhotep?secret="
