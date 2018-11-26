import pytest

from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from twilio.base.exceptions import TwilioException, TwilioRestException


from tests.utils import (
    get_token_from_response,
    get_username_from_jwt,
    header_template,
    login,
)
from trench.utils import create_otp_code, generate_backup_codes


User = get_user_model()



@pytest.mark.django_db
def test_ephemeral_token_verification(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    secret = active_user_with_email_otp.mfa_methods.first().secret
    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    assert response.status_code == 200
    assert get_username_from_jwt(response) == getattr(
        active_user_with_email_otp,
        User.USERNAME_FIELD,
    )


@pytest.mark.django_db
def test_wrong_second_step_verification_with_empty_code(
    active_user_with_email_otp
):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': '',
        },
        format='json',
    )
    msg_error = 'This field may not be blank.'
    assert response.status_code == 400
    assert response.data.get('code')[0] == msg_error


@pytest.mark.django_db
def test_wrong_second_step_verification_with_wrong_code(
    active_user_with_email_otp
):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': 'test',
        },
        format='json',
    )
    code_error = 'invalid_code'
    assert response.status_code == 400
    assert response.data.get('non_field_errors')[0].code == code_error


@pytest.mark.django_db
def test_wrong_second_step_verification_with_ephemeral_token(
    active_user_with_email_otp
):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    secret = active_user_with_email_otp.mfa_methods.first().secret
    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token') + 'wrong',
            'code': create_otp_code(secret),
        },
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_second_method_activation(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    secret = active_user_with_email_otp.mfa_methods.first().secret
    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    assert response.status_code == 200
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )

    # This user should have 1 methods, so we check that it has 1 methods.
    assert len(active_user_with_email_otp.mfa_methods.all()) == 1
    try:
        response = client.post(
            path='/auth/sms/activate/',
            data={
                'phone_number': '555-555-555',
            },
            format='json',
        )
    except (TwilioRestException, TwilioException):
        # twilio rises this exception in test, but the new mfa_method is
        # created anyway.
        pass

    # Now we check that the user has a new method after the activation.
    assert len(active_user_with_email_otp.mfa_methods.all()) == 2


@pytest.mark.django_db
def test_second_method_activation_already_active(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    secret = active_user_with_email_otp.mfa_methods.first().secret
    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    assert response.status_code == 200
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )

    # This user should have 1 methods, so we check that it has 1 methods.
    assert len(active_user_with_email_otp.mfa_methods.all()) == 1
    response = client.post(
        path='/auth/email/activate/',

        format='json',
    )
    error_msg = 'MFA method already active.'
    assert response.status_code == 400
    assert response.data.get('error') == error_msg


@pytest.mark.django_db
def test_use_backup_code(active_user_with_backup_codes):
    client = APIClient()
    first_step = login(active_user_with_backup_codes)
    backup_code = active_user_with_backup_codes.mfa_methods.first(
    ).backup_codes.split(',')[0]

    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': backup_code,
        },
        format='json',
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_activation_otp(active_user):
    client = APIClient()
    first_step = login(active_user)
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(first_step))
    )
    response = client.post(
        path='/auth/email/activate/',
        format='json',
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_activation_otp_confirm_wrong(active_user):
    client = APIClient()
    first_step = login(active_user)
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(first_step))
    )
    response = client.post(
        path='/auth/email/activate/',
        format='json',
    )
    response = client.post(
        path='/auth/email/activate/confirm/',
        data={'code': 'test00'},
        format='json',
    )
    assert response.status_code == 400
    error_code = 'code_invalid_or_expired'
    assert error_code == response.data.get('code')[0].code


@pytest.mark.django_db
def test_confirm_activation_otp(active_user):
    client = APIClient()
    login_response = login(active_user)
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    client.post(
        path='/auth/email/activate/',
        format='json',
    )
    # Until here only make user create a second step confirmation
    active_user_method = active_user.mfa_methods.first()
    active_user_method.is_primary = True
    active_user_method.is_active = True
    active_user_method.save()
    # We manually activate the method
    first_step = login(active_user)
    secret = active_user.mfa_methods.first().secret
    code = create_otp_code(secret)
    response = client.post(
        path='/auth/email/activate/confirm/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': code,
        },
        format='json',
    )
    # Confirm the response is OK and user gets 5 backup codes
    assert response.status_code == 200
    assert len(response.json().get('backup_codes')) == 5


@pytest.mark.django_db
def test_deactivation_otp(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    secret = active_user_with_email_otp.mfa_methods.first().secret
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/email/deactivate/',
        format='json',
    )
    assert response.status_code == 204
    assert not active_user_with_email_otp.mfa_methods.first().is_active


@pytest.mark.django_db
def test_deactivation_otp_already_disabled_method(
    active_user_with_email_and_inactive_other_methods_otp,
):
    client = APIClient()
    first_step = login(active_user_with_email_and_inactive_other_methods_otp)
    secret = active_user_with_email_and_inactive_other_methods_otp.mfa_methods.first().secret  # noqa
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/sms/deactivate/',
        format='json',
    )
    msg_error = 'Method already disabled.'
    assert response.status_code == 400
    assert response.data.get('error') == msg_error


@pytest.mark.django_db
def test_new_method_after_deactivation(active_user_with_many_otp_methods):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = \
        active_user_with_many_otp_methods.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/email/deactivate/',
        data={'new_primary_method': 'sms'},
        format='json',
    )
    new_primary_method = active_user_with_many_otp_methods.mfa_methods.filter(
        is_primary=True,
    )[0]
    assert response.status_code == 204
    assert first_primary_method != new_primary_method


@pytest.mark.django_db
def test_new_method_after_deactivation_same_method_wrong(
    active_user_with_many_otp_methods
):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = \
        active_user_with_many_otp_methods.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/email/deactivate/',
        data={'new_primary_method': 'email'},
        format='json',
    )

    assert response.status_code == 400
    error_code = 'new_primary_same_as_old'
    assert response.data.get('new_primary_method')[0].code == error_code


@pytest.mark.django_db
def test_new_method_after_deactivation_user_doesnt_have_method(
    active_user_with_many_otp_methods
):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = \
        active_user_with_many_otp_methods.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/email/deactivate/',
        data={'new_primary_method': 'test'},
        format='json',
    )

    assert response.status_code == 400
    error_code = 'method_not_registered_for_user'
    assert response.data.get('new_primary_method')[0].code == error_code


@pytest.mark.django_db
def test_change_primary_method(active_user_with_many_otp_methods):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = \
        active_user_with_many_otp_methods.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/mfa/change-primary-method/',
        data={
            'method': 'sms',
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    new_primary_method = active_user_with_many_otp_methods.mfa_methods.filter(
        is_primary=True,
    )[0]
    assert response.status_code == 200
    assert first_primary_method != new_primary_method
    assert new_primary_method.name == 'sms'


@pytest.mark.django_db
def test_change_primary_method_with_backup_code(
    active_user_with_many_otp_methods,
):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = \
        active_user_with_many_otp_methods.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/mfa/change-primary-method/',
        data={
            'method': 'sms',
            'code': first_primary_method.backup_codes.split(',')[0],
        },
        format='json',
    )
    new_primary_method = active_user_with_many_otp_methods.mfa_methods.filter(
        is_primary=True,
    )[0]
    assert response.status_code == 200
    assert first_primary_method != new_primary_method
    assert new_primary_method.name == 'sms'


@pytest.mark.django_db
def test_change_primary_method_to_invalid_wrong(active_user_with_many_otp_methods):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = \
        active_user_with_many_otp_methods.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/mfa/change-primary-method/',
        data={
            'method': 'sms',
            'code': 'test',
        },
        format='json',
    )
    error_code = 'invalid_code'
    assert response.status_code == 400
    assert response.data.get('non_field_errors')[0].code == error_code


@pytest.mark.django_db
def test_change_primary_method_to_inactive(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = \
        active_user_with_email_otp.mfa_methods.filter(
            is_primary=True,
        )[0]
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/mfa/change-primary-method/',
        data={
            'method': 'sms',
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    error_code = 'missing_method'
    assert response.status_code == 400
    assert response.data.get('non_field_errors')[0].code == error_code


@pytest.mark.django_db
def test_change_primary_disabled_method_wrong(active_user):
    client = APIClient()
    login_response = client.post(
        path='/auth/login/',
        data={
            'username': getattr(
                active_user,
                User.USERNAME_FIELD,
            ),
            'password': 'secretkey',
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/mfa/change-primary-method/',
        data={
            'method': 'sms',
            'code': 'code',
        },
        format='json',
    )
    error_code = 'not_enabled'
    assert response.status_code == 400
    assert response.data.get('non_field_errors')[0].code == error_code


@pytest.mark.django_db
def test_confirm_activation_otp_with_backup_code(
    active_user_with_backup_codes,
):
    client = APIClient()
    first_step = login(active_user_with_backup_codes)
    backup_code = active_user_with_backup_codes.mfa_methods.first(
    ).backup_codes.split(',')[0]

    response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': backup_code,
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(response))
    )
    try:
        response = client.post(
            path='/auth/sms/activate/',
            data={
                'phone_number': '555-555-555',
            },
            format='json',
        )
    except (TwilioRestException, TwilioException):
        # twilio rises this exception in test, but the new mfa_method is
        # created anyway.
        pass
    sms_method = active_user_with_backup_codes.mfa_methods.all()[1]
    sms_method.backup_codes = generate_backup_codes()
    sms_method.save()
    backup_code = sms_method.backup_codes.split(',')[0]
    response = client.post(
        path='/auth/sms/activate/confirm/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': backup_code,
        },
        format='json',
    )
    # Confirm the response is OK and user gets 5 backup codes
    assert response.status_code == 200
    assert len(response.json().get('backup_codes')) == 5


@pytest.mark.django_db
def test_request_codes(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.first()
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )

    response = client.post(
        path='/auth/code/request/',
        data={
            'method': 'email',
        },
        format='json',
    )
    expected_msg = 'Email message with MFA code had been sent.'
    assert response.status_code == 200
    assert response.data.get('message') == expected_msg


@pytest.mark.django_db
def test_request_codes_wrong(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.first()
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )

    response = client.post(
        path='/auth/code/request/',
        data={
            'method': 'sms',
        },
        format='json',
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_request_code_non_existing_method(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    first_primary_method = active_user_with_email_otp.mfa_methods.first()
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )

    response = client.post(
        path='/auth/code/request/',
        data={
            'method': 'test',
        },
        format='json',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_backup_codes_regeneration(active_user_with_backup_codes):
    client = APIClient()
    first_step = login(active_user_with_backup_codes)
    first_primary_method = active_user_with_backup_codes.mfa_methods.first()
    old_backup_codes = first_primary_method.backup_codes
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/email/codes/regenerate/',
        format='json',
    )
    new_backup_codes = \
        active_user_with_backup_codes.mfa_methods.first().backup_codes
    assert response.status_code == 200
    assert old_backup_codes != new_backup_codes


@pytest.mark.django_db
def test_backup_codes_regeneration_disabled_method(
    active_user_with_many_otp_methods,
):
    client = APIClient()
    first_step = login(active_user_with_many_otp_methods)
    first_primary_method = active_user_with_many_otp_methods.mfa_methods.filter(
        is_primary=True,
    )[0]
    sms_method = active_user_with_many_otp_methods.mfa_methods.get(
        name='sms',
    )
    sms_method.is_active = False
    sms_method.save()
    login_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(first_primary_method.secret),
        },
        format='json',
    )
    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_response))
    )
    response = client.post(
        path='/auth/sms/codes/regenerate/',
        format='json',
    )
    error_msg = 'Method is disabled.'
    assert response.status_code == 400
    assert response.data.get('error') == error_msg


@pytest.mark.django_db
def test_get_mfa_config():
    client = APIClient()
    response = client.get(
        path='/auth/mfa/config/',
        format='json',
    )
    assert response.status_code == 200

@pytest.mark.django_db
def test_ephemeral_token_verification_simple_jwt(active_user_with_email_otp):
    client = APIClient()
    first_step = login(active_user_with_email_otp)
    secret = active_user_with_email_otp.mfa_methods.first().secret
    response = client.post(
        path='/simplejwt-auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    assert response.status_code == 200
    assert get_username_from_jwt(response, 'access') == getattr(
        active_user_with_email_otp,
        User.USERNAME_FIELD,
    )
