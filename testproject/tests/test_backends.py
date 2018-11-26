import pytest

from django.contrib.auth import get_user_model
from smsapi.exception import ClientException, SendException

from trench.backends.sms_api import SmsAPIBackend

User = get_user_model()


@pytest.mark.django_db
def test_smsapi_backend_without_credentials(
    active_user_with_sms_otp,
    settings,
):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name='sms')
    conf = settings.TRENCH_AUTH['MFA_METHODS']['sms']

    with pytest.raises(ClientException) as exc_info:
        SmsAPIBackend(
            user=active_user_with_sms_otp,
            obj=auth_method,
            conf=conf,
        ).dispatch_message()

    assert 'Credentials are required.' == exc_info.value.message


@pytest.mark.django_db
def test_smsapi_backend_with_wrong_credentials(
    active_user_with_sms_otp,
    settings,
):
    auth_method = active_user_with_sms_otp.mfa_methods.get(name='sms')
    conf = settings.TRENCH_AUTH['MFA_METHODS']['sms']

    settings.TRENCH_AUTH['MFA_METHODS']['sms']['SMSAPI_ACCESS_TOKEN'] = 'wrong-token'

    with pytest.raises(SendException) as exc_info:
        SmsAPIBackend(
            user=active_user_with_sms_otp,
            obj=auth_method,
            conf=conf,
        ).dispatch_message()

    assert 'Authorization failed' == exc_info.value.message


