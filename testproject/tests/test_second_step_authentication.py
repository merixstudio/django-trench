import pytest

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

import time
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
)
from rest_framework.test import APIClient
from twilio.base.exceptions import TwilioException, TwilioRestException

from tests.utils import (
    PATH_AUTH_JWT_LOGIN,
    PATH_AUTH_JWT_LOGIN_CODE,
    get_token_from_response,
    get_username_from_jwt,
    header_template,
    login,
)
from trench.backends.provider import get_mfa_handler
from trench.command.generate_backup_codes import generate_backup_codes_command


User = get_user_model()


@pytest.mark.django_db
def test_custom_validity_period(active_user_with_email_otp, settings):
    settings.TRENCH_AUTH["MFA_METHODS"]["email"]["VALIDITY_PERIOD"] = 3

    client = APIClient()
    first_step = login(active_user_with_email_otp)
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    code = handler.create_code()
    time.sleep(3)
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": code,
        },
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )

    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_ephemeral_token_verification(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    assert get_username_from_jwt(response) == getattr(
        active_user_with_email_otp,
        User.USERNAME_FIELD,
    )


@pytest.mark.django_db
def test_wrong_second_step_verification_with_empty_code(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": "",
        },
        format="json",
    )
    msg_error = "This field may not be blank."
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0] == msg_error


@pytest.mark.django_db
def test_wrong_second_step_verification_with_wrong_code(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": "test",
        },
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data.get("error") == "Invalid or expired code."


@pytest.mark.django_db
def test_wrong_second_step_verification_with_ephemeral_token(
    active_user_with_email_otp,
):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token") + "wrong",
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_second_method_activation(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )

    # This user should have 1 methods, so we check that it has 1 methods.
    assert len(active_user_with_email_otp.mfa_methods.all()) == 1
    try:
        client.post(
            path="/auth/sms_twilio/activate/",
            data={
                "phone_number": "555-555-555",
            },
            format="json",
        )
    except TwilioException:
        # Twilio will raise exception because the secret key used is invalid
        pass
    # Now we check that the user has a new method after the activation.
    assert len(active_user_with_email_otp.mfa_methods.all()) == 2


@pytest.mark.django_db
def test_second_method_activation_already_active(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )

    # This user should have 1 methods, so we check that it has 1 methods.
    assert len(active_user_with_email_otp.mfa_methods.all()) == 1
    response = client.post(
        path="/auth/email/activate/",
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("error") == "MFA method already active."


@pytest.mark.django_db
def test_use_backup_code(active_user_with_encrypted_backup_codes):
    client = APIClient()
    active_user, backup_codes = active_user_with_encrypted_backup_codes
    first_step = login(active_user)

    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": backup_codes.pop(),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_activation_otp(active_user):
    client = APIClient()
    first_step = login(active_user)
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(first_step))
    )
    response = client.post(
        path="/auth/email/activate/",
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_activation_otp_confirm_wrong(active_user):
    client = APIClient()
    first_step = login(active_user)
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(first_step))
    )
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
    client = APIClient()
    login_response = login(active_user)
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    client.post(
        path="/auth/email/activate/",
        format="json",
    )
    # Until here only make user create a second step confirmation
    active_user_method = active_user.mfa_methods.first()
    active_user_method.is_primary = True
    active_user_method.is_active = False
    active_user_method.save()
    # We manually activate the method
    first_step = login(active_user)
    handler = get_mfa_handler(mfa_method=active_user.mfa_methods.first())
    response = client.post(
        path="/auth/email/activate/confirm/",
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    # Confirm the response is OK and user gets 5 backup codes
    assert response.status_code == HTTP_200_OK
    assert len(response.json().get("backup_codes")) == 5


@pytest.mark.django_db
def test_deactivation_of_primary_method(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    handler = get_mfa_handler(mfa_method=active_user_with_email_otp.mfa_methods.first())
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/email/deactivate/",
        data={
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_deactivation_of_secondary_method(active_user_with_many_otp_methods):
    client = APIClient()
    user, _ = active_user_with_many_otp_methods
    first_step = login(user)
    mfa_method_to_be_deactivated = user.mfa_methods.filter(is_primary=False).first()
    handler = get_mfa_handler(mfa_method=mfa_method_to_be_deactivated)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path=f"/auth/{mfa_method_to_be_deactivated.name}/deactivate/",
        data={
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == 204
    mfa_method_to_be_deactivated.refresh_from_db()
    assert not mfa_method_to_be_deactivated.is_active


@pytest.mark.django_db
def test_deactivation_of_disabled_method(
    active_user_with_email_and_inactive_other_methods_otp,
):
    client = APIClient()
    first_step = login(active_user_with_email_and_inactive_other_methods_otp)
    mfa = active_user_with_email_and_inactive_other_methods_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=mfa)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/sms_twilio/deactivate/",
        data={
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "not_enabled"


@pytest.mark.django_db
def test_change_primary_method(active_user_with_many_otp_methods):
    client = APIClient()
    active_user, _ = active_user_with_many_otp_methods
    first_step = login(active_user)
    primary_mfa = active_user.mfa_methods.filter(is_primary=True)[0]
    handler = get_mfa_handler(mfa_method=primary_mfa)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": "sms_twilio",
            "code": handler.create_code(),
        },
        format="json",
    )
    new_primary_method = active_user.mfa_methods.filter(
        is_primary=True,
    )[0]
    assert response.status_code == 204
    assert primary_mfa != new_primary_method
    assert new_primary_method.name == "sms_twilio"


@pytest.mark.django_db
def test_change_primary_method_with_backup_code(
    active_user_with_many_otp_methods,
):
    client = APIClient()
    active_user, backup_code = active_user_with_many_otp_methods
    first_step = login(active_user)
    first_primary_method = active_user.mfa_methods.filter(is_primary=True)[0]
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": "sms_twilio",
            "code": backup_code,
        },
        format="json",
    )
    new_primary_method = active_user.mfa_methods.filter(
        is_primary=True,
    )[0]
    assert response.status_code == 204
    assert first_primary_method != new_primary_method
    assert new_primary_method.name == "sms_twilio"


@pytest.mark.django_db
def test_change_primary_method_to_invalid_wrong(active_user_with_many_otp_methods):
    client = APIClient()
    active_user, _ = active_user_with_many_otp_methods
    first_step = login(active_user)
    first_primary_method = active_user.mfa_methods.filter(is_primary=True)[0]
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": "sms_twilio",
            "code": "test",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "code_invalid_or_expired"


@pytest.mark.django_db
def test_change_primary_method_to_inactive(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.filter(
        is_primary=True
    )[0]
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
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
    assert response.data.get("error") == "Requested MFA method does not exist."


@pytest.mark.django_db
def test_change_primary_disabled_method_wrong(active_user):
    client = APIClient()
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN,
        data={
            "username": getattr(
                active_user,
                User.USERNAME_FIELD,
            ),
            "password": "secretkey",
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/mfa/change-primary-method/",
        data={
            "method": "sms_twilio",
            "code": "code",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data[0].code == "mfa_method_does_not_exist"


@pytest.mark.django_db
def test_confirm_activation_otp_with_backup_code(
    active_user_with_encrypted_backup_codes,
):
    client = APIClient()
    active_user, backup_codes = active_user_with_encrypted_backup_codes
    first_step = login(active_user)

    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": backup_codes.pop(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )
    try:
        response = client.post(
            path="/auth/sms_twilio/activate/",
            data={
                "phone_number": "555-555-555",
            },
            format="json",
        )
    except (TwilioRestException, TwilioException):
        # twilio rises this exception in test, but the new mfa_method is
        # created anyway.
        pass

    backup_codes = generate_backup_codes_command()
    sms_method = active_user.mfa_methods.all()[1]
    sms_method.backup_codes = [make_password(_) for _ in backup_codes]
    sms_method.save()
    response = client.post(
        path="/auth/sms_twilio/activate/confirm/",
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": next(iter(backup_codes)),
        },
        format="json",
    )
    # Confirm the response is OK and user gets 5 backup codes
    assert response.status_code == HTTP_200_OK
    assert len(response.json().get("backup_codes")) == 5


@pytest.mark.django_db
def test_request_codes(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )

    response = client.post(
        path="/auth/code/request/",
        data={"method": "email"},
        format="json",
    )
    expected_msg = "Email message with MFA code has been sent."
    assert response.status_code == HTTP_200_OK
    assert response.data.get("details") == expected_msg


@pytest.mark.django_db
def test_request_codes_wrong(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )

    response = client.post(
        path="/auth/code/request/",
        data={
            "method": "sms_twilio",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("error") == "Requested MFA method does not exist."


@pytest.mark.django_db
def test_request_code_non_existing_method(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )

    response = client.post(
        path="/auth/code/request/",
        data={
            "method": "test",
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_backup_codes_regeneration(active_user_with_encrypted_backup_codes):
    client = APIClient()
    active_user, _ = active_user_with_encrypted_backup_codes
    first_step = login(active_user)
    first_primary_method = active_user.mfa_methods.first()
    old_backup_codes = first_primary_method.backup_codes
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
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


@pytest.mark.django_db
def test_backup_codes_regeneration_without_otp(active_user_with_encrypted_backup_codes):
    client = APIClient()
    active_user, _ = active_user_with_encrypted_backup_codes
    first_step = login(active_user)
    first_primary_method = active_user.mfa_methods.first()
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(path="/auth/email/codes/regenerate/", format="json")
    assert response.data.get("code")[0].code == "required"
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_backup_codes_regeneration_disabled_method(
    active_user_with_many_otp_methods,
):
    client = APIClient()
    active_user, _ = active_user_with_many_otp_methods
    first_step = login(active_user)
    first_primary_method = active_user.mfa_methods.filter(
        is_primary=True,
    )[0]
    sms_method = active_user.mfa_methods.get(
        name="sms_twilio",
    )
    sms_method.is_active = False
    sms_method.save()
    handler = get_mfa_handler(mfa_method=first_primary_method)
    login_response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(
            get_token_from_response(login_response)
        )
    )
    response = client.post(
        path="/auth/sms_twilio/codes/regenerate/",
        data={
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.data.get("code")[0].code == "not_enabled"


@pytest.mark.django_db
def test_yubikey(active_user_with_yubi, offline_yubikey):
    first_step_response = login(active_user_with_yubi)
    handler = get_mfa_handler(mfa_method=active_user_with_yubi.mfa_methods.first())
    response = APIClient().post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step_response.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_yubikey_exception(active_user_with_yubi, fake_yubikey):
    first_step_response = login(active_user_with_yubi)
    handler = get_mfa_handler(mfa_method=active_user_with_yubi.mfa_methods.first())
    response = APIClient().post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": first_step_response.data.get("ephemeral_token"),
            "code": handler.create_code(),
        },
        format="json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.data.get("error") is not None


@pytest.mark.django_db
def test_confirm_yubikey_activation_with_backup_code(
    active_user_with_encrypted_backup_codes,
):
    client = APIClient()
    active_user, backup_codes = active_user_with_encrypted_backup_codes
    first_step = login(active_user)
    ephemeral_token = first_step.data.get("ephemeral_token")
    response = client.post(
        path=PATH_AUTH_JWT_LOGIN_CODE,
        data={
            "ephemeral_token": ephemeral_token,
            "code": backup_codes.pop(),
        },
        format="json",
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )
    client.post(
        path="/auth/yubi/activate/",
        format="json",
    )
    response = client.post(
        path="/auth/yubi/activate/confirm/",
        data={
            "ephemeral_token": ephemeral_token,
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
