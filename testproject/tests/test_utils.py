import pytest

from trench.utils import (
    UserTokenGenerator,
    create_qr_link,
    get_innermost_object,
)


@pytest.mark.django_db
def test_token_obj_without_token():
    token = UserTokenGenerator()
    assert token.check_token(None) is None


@pytest.mark.django_db
def test_unexisting_user():
    token = UserTokenGenerator()
    assert token.check_token('test') is None


@pytest.mark.django_db
def test_create_qr_link(active_user_with_email_otp):
    secret = active_user_with_email_otp.mfa_methods.first().secret
    qr_link = create_qr_link(
        secret,
        active_user_with_email_otp,
    )
    assert type(qr_link) == str
    assert active_user_with_email_otp.username in qr_link
    assert secret in qr_link


@pytest.mark.django_db
def test_innermost_object_test(active_user):
    with pytest.raises(AttributeError):
        get_innermost_object(active_user, dotted_path='test')
