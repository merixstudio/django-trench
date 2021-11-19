import pytest

from django.test import Client
from django.urls import reverse

from collections import OrderedDict
from rest_framework.status import HTTP_400_BAD_REQUEST

from trench.command.set_primary_mfa_method import set_primary_mfa_method_command
from trench.exceptions import (
    MethodHandlerMissingError,
    MFAMethodAlreadyActiveError,
    MFAPrimaryMethodInactiveError,
    OTPCodeMissingError,
    RestrictedCharInBackupCodeError,
)
from trench.models import MFAMethod
from trench.serializers import (
    MFAMethodActivationConfirmationValidator,
    ProtectedActionValidator,
    RequestBodyValidator,
)
from trench.settings import DEFAULTS, TrenchAPISettings


def test_restricted_char_in_backup_code_error():
    settings = TrenchAPISettings(
        user_settings={"BACKUP_CODES_CHARACTERS": ","}, defaults=DEFAULTS
    )
    with pytest.raises(RestrictedCharInBackupCodeError):
        assert settings.BACKUP_CODES_CHARACTERS is not None


def test_method_handler_missing_error():
    settings = TrenchAPISettings(
        user_settings={"MFA_METHODS": {"method_without_handler": {}}}, defaults=DEFAULTS
    )
    with pytest.raises(MethodHandlerMissingError):
        assert settings.MFA_METHODS["method_without_handler"] is None


def test_code_missing_error():
    validator = ProtectedActionValidator(mfa_method_name="yubi", user=None)
    with pytest.raises(OTPCodeMissingError):
        validator.validate_code(value="")


def test_request_body_validator():
    validator = RequestBodyValidator()
    with pytest.raises(NotImplementedError):
        validator.create(validated_data=OrderedDict())
    with pytest.raises(NotImplementedError):
        validator.update(instance=MFAMethod(), validated_data=OrderedDict())


def test_protected_action_validator():
    validator = ProtectedActionValidator(mfa_method_name="yubi", user=None)
    with pytest.raises(NotImplementedError):
        validator._validate_mfa_method(mfa=MFAMethod())


def test_mfa_method_activation_validator():
    validator = MFAMethodActivationConfirmationValidator(
        mfa_method_name="yubi", user=None
    )
    with pytest.raises(MFAMethodAlreadyActiveError):
        validator._validate_mfa_method(mfa=MFAMethod(is_active=True))


@pytest.mark.django_db
def test_primary_method_inactive_error(
    active_user_with_email_and_inactive_other_methods_otp,
):
    with pytest.raises(MFAPrimaryMethodInactiveError):
        set_primary_mfa_method_command(
            user_id=active_user_with_email_and_inactive_other_methods_otp.id,
            name="sms_twilio",
        )


@pytest.mark.django_db
def test_user_account_disabled_error(active_user_with_application_otp):
    active_user_with_application_otp.is_active = False
    active_user_with_application_otp.save()
    client = Client()
    response = client.post(
        reverse("generate-code-jwt"),
        data={"username": "imhotep", "password": "secretkey"},
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
