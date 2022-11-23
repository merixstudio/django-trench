import pytest

from django.contrib.auth import get_user_model

from trench.backends.application import ApplicationMessageDispatcher
from trench.backends.aws import AWSMessageDispatcher
from trench.backends.sms_api import SMSAPIMessageDispatcher
from trench.backends.twilio import TwilioMessageDispatcher
from trench.backends.yubikey import YubiKeyMessageDispatcher
from trench.exceptions import MissingConfigurationError


User = get_user_model()


@pytest.mark.django_db
def test_twilio_backend_without_credentials(active_user_with_twilio_otp, settings):
    auth_method = active_user_with_twilio_otp.mfa_methods.get(name="sms_twilio")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]
    response = TwilioMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details")[:23] == "Unable to create record"


@pytest.mark.django_db
def test_sms_api_backend_without_credentials(active_user_with_sms_otp, settings):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name="sms_api")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_api"]
    response = SMSAPIMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details") == "Authorization failed"


@pytest.mark.django_db
def test_sms_api_backend_with_wrong_credentials(active_user_with_sms_otp, settings):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name="sms_api")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_api"]
    settings.TRENCH_AUTH["MFA_METHODS"]["sms_api"][
        "SMSAPI_ACCESS_TOKEN"
    ] = "wrong-token"
    response = SMSAPIMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert "Authorization failed" == response.data.get("details")


@pytest.mark.django_db
def test_sms_backend_misconfiguration_error(active_user_with_twilio_otp, settings):
    auth_method = active_user_with_twilio_otp.mfa_methods.get(name="sms_twilio")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]
    current_source = settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]["SOURCE_FIELD"]
    settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]["SOURCE_FIELD"] = "invalid.source"
    with pytest.raises(MissingConfigurationError):
        SMSAPIMessageDispatcher(mfa_method=auth_method, config=conf).dispatch_message()
    settings.TRENCH_AUTH["MFA_METHODS"]["sms_twilio"]["SOURCE_FIELD"] = current_source


@pytest.mark.django_db
def test_application_backend_generating_url_successfully(
    active_user_with_application_otp, settings
):
    auth_method = active_user_with_application_otp.mfa_methods.get(name="app")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["app"]
    response = ApplicationMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert (
        response.data.get("details")[:44]
        == "otpauth://totp/MyApplication:imhotep?secret="
    )


@pytest.mark.django_db
def test_yubikey_backend(active_user_with_many_otp_methods, settings):
    user, code = active_user_with_many_otp_methods
    config = settings.TRENCH_AUTH["MFA_METHODS"]["yubi"]
    auth_method = user.mfa_methods.get(name="yubi")
    dispatcher = YubiKeyMessageDispatcher(mfa_method=auth_method, config=config)
    dispatcher.confirm_activation(code)


@pytest.mark.django_db
def test_sms_aws_backend_without_credentials(active_user_with_sms_aws_otp, settings):
    auth_method = active_user_with_sms_aws_otp.mfa_methods.get(name="sms_aws")
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["sms_aws"]
    response = AWSMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details")[:38] == "Could not connect to the endpoint URL:"
