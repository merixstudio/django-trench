import pytest

from django.contrib.auth import get_user_model

from flaky import flaky
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.test import APIClient
from time import sleep
from twilio.base.exceptions import TwilioException, TwilioRestException

from tests.utils import TrenchAPIClient
from trench.backends.provider import get_mfa_handler
from trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod


User = get_user_model()


@pytest.mark.django_db
def test_mfa_method_manager(active_user):
    with pytest.raises(MFAMethodDoesNotExistError):
        MFAMethod.objects.get_primary_active_name(user_id=active_user.id)


@pytest.mark.django_db
def test_mfa_model(active_user_with_email_otp):
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    assert "email" in str(mfa_method)

    mfa_method.backup_codes = ["test1", "test2"]
    assert mfa_method.backup_codes == ["test1", "test2"]
    mfa_method.backup_codes = ""


@pytest.mark.django_db
def test_custom_validity_period(active_user_with_email_otp, settings):
    ORIGINAL_VALIDITY_PERIOD = settings.TRENCH_AUTH["MFA_METHODS"]["email"][
        "VALIDITY_PERIOD"
    ]
    settings.TRENCH_AUTH["MFA_METHODS"]["email"]["VALIDITY_PERIOD"] = 3

    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client = TrenchAPIClient()
    response_first_step = client._first_factor_request(user=active_user_with_email_otp)
    ephemeral_token = client._extract_ephemeral_token_from_response(
        response=response_first_step
    )
    handler = get_mfa_handler(mfa_method=mfa_method)
    code = handler.create_code()

    sleep(3)

    response_second_step = client._second_factor_request(
        code=code, ephemeral_token=ephemeral_token
    )
    assert response_second_step.status_code == HTTP_401_UNAUTHORIZED

    response_second_step = client._second_factor_request(
        handler=handler, ephemeral_token=ephemeral_token
    )
    assert response_second_step.status_code == HTTP_200_OK

    settings.TRENCH_AUTH["MFA_METHODS"]["email"][
        "VALIDITY_PERIOD"
    ] = ORIGINAL_VALIDITY_PERIOD


@flaky
@pytest.mark.django_db
def test_ephemeral_token_verification(active_user_with_email_otp):
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client = TrenchAPIClient()
    response = client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    assert response.status_code == HTTP_200_OK
    assert client.get_username_from_jwt(response=response) == getattr(
        active_user_with_email_otp,
        User.USERNAME_FIELD,
    )


@pytest.mark.django_db
def test_wrong_second_step_verification_with_empty_code(active_user_with_email_otp):
    client = TrenchAPIClient()
    response_first_step = client._first_factor_request(user=active_user_with_email_otp)
    ephemeral_token = client._extract_ephemeral_token_from_response(
        response=response_first_step
    )
    response_second_step = client._second_factor_request(
        code="", ephemeral_token=ephemeral_token
    )
    msg_error = "This field may not be blank."
    assert response_second_step.status_code == HTTP_400_BAD_REQUEST
    assert response_second_step.data.get("code")[0] == msg_error


@pytest.mark.django_db
def test_wrong_second_step_verification_with_wrong_code(active_user_with_email_otp):
    client = TrenchAPIClient()
    response_first_step = client._first_factor_request(user=active_user_with_email_otp)
    ephemeral_token = client._extract_ephemeral_token_from_response(
        response=response_first_step
    )
    response_second_step = client._second_factor_request(
        code="invalid", ephemeral_token=ephemeral_token
    )
    assert response_second_step.status_code == HTTP_401_UNAUTHORIZED
    assert response_second_step.data.get("error") == "Invalid or expired code."


@pytest.mark.django_db
def test_wrong_second_step_verification_with_ephemeral_token(
    active_user_with_email_otp,
):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    response = client._second_factor_request(
        code=handler.create_code(), ephemeral_token="invalid"
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@flaky
@pytest.mark.django_db
def test_second_method_activation(active_user_with_email_otp):
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client = TrenchAPIClient()
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    assert len(active_user_with_email_otp.mfa_methods.all()) == 1
    try:
        client.post(
            path="/auth/sms_twilio/activate/",
            data={"phone_number": "555-555-555"},
            format="json",
        )
    except TwilioException:
        # Twilio will raise exception because the secret key used is invalid
        pass
    assert len(active_user_with_email_otp.mfa_methods.all()) == 2


@flaky
@pytest.mark.django_db
def test_second_method_activation_already_active(active_user_with_email_otp):
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client = TrenchAPIClient()
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    assert len(active_user_with_email_otp.mfa_methods.all()) == 1
    response = client.post(
        path="/auth/email/activate/",
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("error") == "MFA method already active."


@pytest.mark.django_db
def test_use_backup_code(active_user_with_encrypted_backup_codes):
    client = TrenchAPIClient()
    active_user, backup_codes = active_user_with_encrypted_backup_codes
    response_first_step = client._first_factor_request(user=active_user)
    ephemeral_token = client._extract_ephemeral_token_from_response(
        response=response_first_step
    )
    response_second_step = client._second_factor_request(
        code=backup_codes.pop(), ephemeral_token=ephemeral_token
    )
    assert response_second_step.status_code == HTTP_200_OK

    mfa_method = active_user.mfa_methods.first()
    assert len(mfa_method.backup_codes) == 7


@pytest.mark.django_db
def test_activation_otp(active_user):
    client = TrenchAPIClient()
    client.authenticate(user=active_user)
    response = client.post(
        path="/auth/email/activate/",
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_activation_otp_confirm_wrong(active_user):
    client = TrenchAPIClient()
    client.authenticate(user=active_user)
    response = client.post(
        path="/auth/email/activate/",
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    response = client.post(
        path="/auth/email/activate/confirm/",
        data={"code": "test00"},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    error_code = "code_invalid_or_expired"
    assert response.data.get("code")[0].code == error_code


@pytest.mark.django_db
def test_confirm_activation_otp(active_user):
    client = TrenchAPIClient()
    client.authenticate(user=active_user)

    # create new MFA method
    client.post(
        path="/auth/email/activate/",
        format="json",
    )
    mfa_method = active_user.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa_method)

    # activate the newly created MFA method
    response = client.post(
        path="/auth/email/activate/confirm/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    assert len(response.data.get("backup_codes")) == 8
    mfa_method.delete()
    assert active_user.mfa_methods.count() == 0


@flaky
@pytest.mark.django_db
def test_deactivation_of_an_only_primary_mfa_method(active_user_with_email_otp):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    response = client.post(
        path="/auth/email/deactivate/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_204_NO_CONTENT


@flaky
@pytest.mark.django_db
def test_deactivation_of_an_only_primary_mfa_method_when_other_mfa_inactive(
    active_user_with_email_and_inactive_other_methods_otp,
):
    client = TrenchAPIClient()
    mfa_method = (
        active_user_with_email_and_inactive_other_methods_otp.mfa_methods.first()
    )
    handler = get_mfa_handler(mfa_method=mfa_method)
    client.authenticate_multi_factor(
        mfa_method=mfa_method,
        user=active_user_with_email_and_inactive_other_methods_otp,
    )
    response = client.post(
        path="/auth/email/deactivate/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_204_NO_CONTENT


@flaky
@pytest.mark.django_db
def test_deactivation_of_primary_mfa_method_when_other_active_mfa_methods(
    active_user_with_email_and_active_other_methods_otp,
):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_and_active_other_methods_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_and_active_other_methods_otp
    )
    response = client.post(
        path="/auth/email/deactivate/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


@flaky
@pytest.mark.django_db
def test_deactivation_of_secondary_method(active_user_with_many_otp_methods):
    user, _ = active_user_with_many_otp_methods
    client = TrenchAPIClient()
    mfa_method = user.mfa_methods.filter(is_primary=False).first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    client.authenticate_multi_factor(mfa_method=mfa_method, user=user)
    response = client.post(
        path=f"/auth/{mfa_method.name}/deactivate/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    mfa_method.refresh_from_db()
    assert not mfa_method.is_active

    # revert changes
    mfa_method.is_active = True
    mfa_method.save()


@flaky
@pytest.mark.django_db
def test_deactivation_of_disabled_method(
    active_user_with_email_and_inactive_other_methods_otp,
):
    user = active_user_with_email_and_inactive_other_methods_otp
    client = TrenchAPIClient()
    mfa_method = user.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    client.authenticate_multi_factor(mfa_method=mfa_method, user=user)
    response = client.post(
        path="/auth/sms_twilio/deactivate/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "not_enabled"


@flaky
@pytest.mark.django_db
def test_change_primary_method(active_user_with_many_otp_methods):
    active_user, _ = active_user_with_many_otp_methods
    client = TrenchAPIClient()
    primary_mfa_method = active_user.mfa_methods.filter(is_primary=True).first()
    sms_twilio_mfa_method = active_user.mfa_methods.filter(name="sms_twilio").first()
    handler = get_mfa_handler(mfa_method=sms_twilio_mfa_method)
    client.authenticate_multi_factor(mfa_method=primary_mfa_method, user=active_user)
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": sms_twilio_mfa_method.name,
            "code": handler.create_code(),
        },
        format="json",
    )
    new_primary_method = active_user.mfa_methods.filter(
        is_primary=True,
    ).first()
    assert response.status_code == HTTP_204_NO_CONTENT
    assert primary_mfa_method != new_primary_method
    assert new_primary_method.name == sms_twilio_mfa_method.name

    # revert changes
    new_primary_method.is_primary = False
    new_primary_method.save()
    primary_mfa_method.is_primary = True
    primary_mfa_method.save()


@flaky
@pytest.mark.django_db
def test_change_primary_method_with_backup_code(
    active_user_with_many_otp_methods,
):
    active_user, backup_code = active_user_with_many_otp_methods
    client = TrenchAPIClient()
    primary_mfa_method = active_user.mfa_methods.filter(is_primary=True).first()
    sms_twilio_mfa_method_name = "sms_twilio"
    client.authenticate_multi_factor(mfa_method=primary_mfa_method, user=active_user)
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": sms_twilio_mfa_method_name,
            "code": backup_code,
        },
        format="json",
    )
    new_primary_method = active_user.mfa_methods.filter(
        is_primary=True,
    ).first()
    assert response.status_code == HTTP_204_NO_CONTENT
    assert primary_mfa_method != new_primary_method
    assert new_primary_method.name == sms_twilio_mfa_method_name

    # revert changes
    new_primary_method.is_primary = False
    new_primary_method.save()
    primary_mfa_method.is_primary = True
    primary_mfa_method.save()


@flaky
@pytest.mark.django_db
def test_change_primary_method_with_invalid_code(active_user_with_many_otp_methods):
    active_user, _ = active_user_with_many_otp_methods
    client = TrenchAPIClient()
    primary_mfa_method = active_user.mfa_methods.filter(is_primary=True).first()
    client.authenticate_multi_factor(mfa_method=primary_mfa_method, user=active_user)
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": "sms_twilio",
            "code": "invalid",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "code_invalid_or_expired"


@flaky
@pytest.mark.django_db
def test_change_primary_method_to_inactive(active_user_with_email_otp):
    client = TrenchAPIClient()
    primary_mfa_method = active_user_with_email_otp.mfa_methods.filter(
        is_primary=True
    ).first()
    handler = get_mfa_handler(mfa_method=primary_mfa_method)
    client.authenticate_multi_factor(
        mfa_method=primary_mfa_method, user=active_user_with_email_otp
    )
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": "sms_twilio",
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "mfa_method_does_not_exist"


@pytest.mark.django_db
def test_confirm_activation_otp_with_backup_code(
    active_user_with_encrypted_backup_codes,
):
    active_user, backup_codes = active_user_with_encrypted_backup_codes
    client = TrenchAPIClient()
    response = client._first_factor_request(user=active_user)
    ephemeral_token = client._extract_ephemeral_token_from_response(response=response)
    response = client._second_factor_request(
        ephemeral_token=ephemeral_token, code=backup_codes.pop()
    )
    assert response.status_code == HTTP_200_OK
    client._update_jwt_from_response(response=response)
    try:
        client.post(
            path="/auth/sms_twilio/activate/",
            data={"phone_number": "555-555-555"},
            format="json",
        )
    except (TwilioRestException, TwilioException):
        # twilio rises this exception in test, but the new mfa_method is
        # created anyway.
        pass

    backup_codes = regenerate_backup_codes_for_mfa_method_command(
        user_id=active_user.id, name="sms_twilio"
    )
    response = client.post(
        path="/auth/sms_twilio/activate/confirm/",
        data={"code": backup_codes.pop()},
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    assert len(response.data.get("backup_codes")) == 8

    # revert changes
    active_user.mfa_methods.filter(name="sms_twilio").delete()


@flaky
@pytest.mark.django_db
def test_request_code_for_active_mfa_method(active_user_with_email_otp):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    response = client.post(
        path="/auth/code/request/",
        data={"method": "email"},
        format="json",
    )
    expected_msg = "Email message with MFA code has been sent."
    assert response.status_code == HTTP_200_OK
    assert response.data.get("details") == expected_msg


@flaky
@pytest.mark.django_db
def test_request_code_for_not_inactive_mfa_method(active_user_with_email_otp):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    response = client.post(
        path="/auth/code/request/",
        data={"method": "sms_twilio"},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("error") == "Requested MFA method does not exist."


@flaky
@pytest.mark.django_db
def test_request_code_for_invalid_mfa_method(active_user_with_email_otp):
    client = TrenchAPIClient()
    mfa_method = active_user_with_email_otp.mfa_methods.first()
    client.authenticate_multi_factor(
        mfa_method=mfa_method, user=active_user_with_email_otp
    )
    response = client.post(
        path="/auth/code/request/",
        data={"method": "invalid"},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


@flaky
@pytest.mark.django_db
def test_backup_codes_regeneration(active_user_with_encrypted_backup_codes):
    active_user, _ = active_user_with_encrypted_backup_codes
    client = TrenchAPIClient()
    mfa_method = active_user.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa_method)
    client.authenticate_multi_factor(mfa_method=mfa_method, user=active_user)
    old_backup_codes = active_user.mfa_methods.first().backup_codes
    response = client.post(
        path="/auth/email/codes/regenerate/",
        data={
            "code": handler.create_code(),
        },
        format="json",
    )
    new_backup_codes = active_user.mfa_methods.first().backup_codes
    assert response.status_code == HTTP_200_OK
    assert old_backup_codes != new_backup_codes


@flaky
@pytest.mark.django_db
def test_backup_codes_regeneration_without_otp(active_user_with_encrypted_backup_codes):
    active_user, _ = active_user_with_encrypted_backup_codes
    client = TrenchAPIClient()
    mfa_method = active_user.mfa_methods.first()
    client.authenticate_multi_factor(mfa_method=mfa_method, user=active_user)
    response = client.post(path="/auth/email/codes/regenerate/", format="json")
    assert response.data.get("code")[0].code == "required"
    assert response.status_code == HTTP_400_BAD_REQUEST


@flaky
@pytest.mark.django_db
def test_backup_codes_regeneration_disabled_method(
    active_user_with_many_otp_methods,
):
    active_user, _ = active_user_with_many_otp_methods
    client = TrenchAPIClient()
    primary_method = active_user.mfa_methods.filter(is_primary=True).first()
    handler = get_mfa_handler(mfa_method=primary_method)
    client.authenticate_multi_factor(mfa_method=primary_method, user=active_user)

    active_user.mfa_methods.filter(name="sms_twilio").update(is_active=False)

    response = client.post(
        path="/auth/sms_twilio/codes/regenerate/",
        data={"code": handler.create_code()},
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "not_enabled"

    # revert changes
    active_user.mfa_methods.filter(name="sms_twilio").update(is_active=True)


@flaky
@pytest.mark.django_db
def test_yubikey(active_user_with_yubi, offline_yubikey):
    client = TrenchAPIClient()
    yubikey_method = active_user_with_yubi.mfa_methods.first()
    response = client.authenticate_multi_factor(
        mfa_method=yubikey_method, user=active_user_with_yubi
    )
    assert response.status_code == HTTP_200_OK


@flaky
@pytest.mark.django_db
def test_yubikey_exception(active_user_with_yubi, fake_yubikey):
    client = TrenchAPIClient()
    yubikey_method = active_user_with_yubi.mfa_methods.first()
    response = client.authenticate_multi_factor(
        mfa_method=yubikey_method, user=active_user_with_yubi
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data.get("error") is not None


@pytest.mark.django_db
def test_confirm_yubikey_activation_with_backup_code(
    active_user_with_encrypted_backup_codes,
):
    active_user, backup_codes = active_user_with_encrypted_backup_codes
    client = TrenchAPIClient()
    response = client._first_factor_request(user=active_user)
    ephemeral_token = client._extract_ephemeral_token_from_response(response=response)
    response = client._second_factor_request(
        ephemeral_token=ephemeral_token, code=backup_codes.pop()
    )
    client._update_jwt_from_response(response=response)
    client.post(
        path="/auth/yubi/activate/",
        format="json",
    )
    response = client.post(
        path="/auth/yubi/activate/confirm/",
        data={
            "code": backup_codes.pop(),
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code") is not None


@pytest.mark.django_db
def test_get_mfa_config():
    client = APIClient()
    response = client.get(
        path="/auth/mfa/config/",
        format="json",
    )
    assert response.status_code == HTTP_200_OK
