import pytest

from trench.utils import (
    UserTokenGenerator,
    create_qr_link,
    get_innermost_object,
    validate_code,
    create_otp_code,
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


@pytest.mark.django_db
def test_validate_code(active_user_with_email_otp):
    email_method = active_user_with_email_otp.mfa_methods.get()
    valid_code = create_otp_code(email_method.secret)

    assert validate_code("123456", email_method) is False
    assert validate_code(valid_code, email_method) is True


@pytest.mark.django_db
def test_validate_code_yubikey(active_user_with_many_otp_methods):
    yubi_method = active_user_with_many_otp_methods.mfa_methods.get(name='yubi')

    assert validate_code("t" * 44, yubi_method) is False
