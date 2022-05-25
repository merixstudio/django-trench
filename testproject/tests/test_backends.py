import pytest

from django.contrib.auth import get_user_model

from tests.conftest import mfa_method_creator
from trench.backends.application import ApplicationMessageDispatcher
from trench.backends.sms_api import SMSAPIMessageDispatcher
from trench.backends.twilio import (
    TwilioCallMessageDispatcher,
    TwilioSMSMessageDispatcher,
)
from trench.backends.yubikey import YubiKeyMessageDispatcher
from trench.exceptions import MissingConfigurationError
from trench.settings import MfaMethods


User = get_user_model()


@pytest.mark.django_db
def test_twilio_sms_backend_without_credentials(
    active_user_with_twilio_sms_otp, settings
):
    auth_method = active_user_with_twilio_sms_otp.mfa_methods.get(
        name=MfaMethods.SMS_TWILIO.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_TWILIO.value]
    response = TwilioSMSMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details")[:23] == "Unable to create record"


@pytest.mark.django_db
def test_twilio_call_backend_without_credentials(
    active_user_with_twilio_call_otp, settings
):
    auth_method = active_user_with_twilio_call_otp.mfa_methods.get(
        name=MfaMethods.CALL_TWILIO.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.CALL_TWILIO.value]
    response = TwilioSMSMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details")[:23] == "Unable to create record"


@pytest.mark.django_db
def test_sms_api_backend_without_credentials(active_user_with_sms_otp, settings):
    auth_method = active_user_with_sms_otp.mfa_methods.get(
        name=MfaMethods.SMS_API.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_API.value]
    response = SMSAPIMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert response.data.get("details") == "Authorization failed"


@pytest.mark.django_db
def test_sms_api_backend_with_wrong_credentials(active_user_with_sms_otp, settings):
    auth_method = active_user_with_sms_otp.mfa_methods.get(
        name=MfaMethods.SMS_API.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_API.value]
    settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_API.value][
        "SMSAPI_ACCESS_TOKEN"
    ] = "wrong-token"
    response = SMSAPIMessageDispatcher(
        mfa_method=auth_method, config=conf
    ).dispatch_message()
    assert "Authorization failed" == response.data.get("details")


@pytest.mark.django_db
def test_twilio_sms_backend_misconfiguration_error(
    active_user_with_twilio_sms_otp, settings
):
    auth_method = active_user_with_twilio_sms_otp.mfa_methods.get(
        name=MfaMethods.SMS_TWILIO.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_TWILIO.value]
    current_source = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_TWILIO.value][
        "SOURCE_FIELD"
    ]
    settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_TWILIO.value][
        "SOURCE_FIELD"
    ] = "invalid.source"
    with pytest.raises(MissingConfigurationError):
        TwilioSMSMessageDispatcher(
            mfa_method=auth_method, config=conf
        ).dispatch_message()
    settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.SMS_TWILIO.value][
        "SOURCE_FIELD"
    ] = current_source


@pytest.mark.django_db
def test_twilio_call_backend_misconfiguration_error(
    active_user_with_twilio_call_otp, settings
):
    auth_method = active_user_with_twilio_call_otp.mfa_methods.get(
        name=MfaMethods.CALL_TWILIO.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.CALL_TWILIO.value]
    current_source = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.CALL_TWILIO.value][
        "SOURCE_FIELD"
    ]
    settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.CALL_TWILIO.value][
        "SOURCE_FIELD"
    ] = "invalid.source"
    with pytest.raises(MissingConfigurationError):
        TwilioCallMessageDispatcher(
            mfa_method=auth_method, config=conf
        ).dispatch_message()
    settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.CALL_TWILIO.value][
        "SOURCE_FIELD"
    ] = current_source


@pytest.mark.django_db
def test_twilio_call_backend(active_user_with_many_otp_methods, settings):
    user, code = active_user_with_many_otp_methods
    mfa_method_creator(
        user=user, method_name=MfaMethods.CALL_TWILIO.value, is_primary=False
    )
    config = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.CALL_TWILIO.value]
    auth_method = user.mfa_methods.get(name=MfaMethods.CALL_TWILIO.value)
    response = TwilioCallMessageDispatcher(
        mfa_method=auth_method, config=config
    ).dispatch_message()
    assert (
        response.data.get("details")
        == "Unable to create record: The requested resource /2010-04-01/Accounts/TEST/Calls.json was not found"
    )


@pytest.mark.django_db
def test_application_backend_generating_url_successfully(
    active_user_with_application_otp, settings
):
    auth_method = active_user_with_application_otp.mfa_methods.get(
        name=MfaMethods.APP.value
    )
    conf = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.APP.value]
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
    config = settings.TRENCH_AUTH["MFA_METHODS"][MfaMethods.YUBI.value]
    auth_method = user.mfa_methods.get(name=MfaMethods.YUBI.value)
    dispatcher = YubiKeyMessageDispatcher(mfa_method=auth_method, config=config)
    dispatcher.confirm_activation(code)
