import pytest

from django.contrib.auth import get_user_model

from rest_framework.test import APIClient


from tests.utils import get_token_from_response, header_template, login
from trench.utils import create_otp_code, create_secret


User = get_user_model()


@pytest.mark.django_db
def test_add_user_mfa(active_user):
    client = APIClient()
    login_request = login(active_user)
    client.credentials(HTTP_AUTHORIZATION=header_template.format(get_token_from_response(login_request)))
    secret = create_secret()
    response = client.post(
        path='/auth/email/activate/',
        data={
            'secret': secret,
            'code': create_otp_code(secret),
            'user': getattr(
                active_user,
                active_user.USERNAME_FIELD,
            )
        },
        format='json',

    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_user_with_many_methods(active_user_with_many_otp_methods):
    client = APIClient()

    initial_active_methods_count = active_user_with_many_otp_methods.mfa_methods.filter(is_active=True).count()

    first_step = login(active_user_with_many_otp_methods)
    primary_method = active_user_with_many_otp_methods.mfa_methods.filter(
        is_primary=True,
    )
    # As user has several methods get first and get sure only 1 is primary
    assert len(primary_method) == 1

    secret = primary_method[0].secret
    second_step_response = client.post(
        path='/auth/login/code/',
        data={
            'token': first_step.data.get('ephemeral_token'),
            'code': create_otp_code(secret),
        },
        format='json',
    )
    # Log in the user in the second step and make sure it is correct
    assert second_step_response.status_code == 200

    client.credentials(
        HTTP_AUTHORIZATION=header_template.format(get_token_from_response(second_step_response))
    )
    active_methods_response = client.get(
        path='/auth/mfa/user-active-methods/',
    )

    # This user should have 3 methods, so we check that return has 3 methods
    assert len(active_methods_response.data) == initial_active_methods_count
