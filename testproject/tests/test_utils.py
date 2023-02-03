import pytest

from trench.backends.application import ApplicationMessageDispatcher
from trench.backends.base import AbstractMessageDispatcher
from trench.backends.provider import get_mfa_handler
from trench.models import MFAMethod
from trench.utils import UserTokenGenerator


@pytest.mark.django_db
def test_empty_token():
    token = UserTokenGenerator()
    assert token.check_token(user=None, token="") is None


@pytest.mark.django_db
def test_invalid_token():
    token = UserTokenGenerator()
    assert token.check_token(user=None, token="test") is None


@pytest.mark.django_db
def test_create_qr_link(active_user_with_many_otp_methods):
    user, _ = active_user_with_many_otp_methods
    mfa_method: MFAMethod = user.mfa_methods.filter(name="app").first()
    handler: ApplicationMessageDispatcher = get_mfa_handler(mfa_method)
    qr_link = handler._create_qr_link(user=user)
    assert type(qr_link) == str
    assert user.username in qr_link
    assert mfa_method.secret in qr_link


@pytest.mark.django_db
def test_innermost_object_test(active_user):
    with pytest.raises(AttributeError):
        AbstractMessageDispatcher._get_innermost_object(active_user, dotted_path="test")


@pytest.mark.django_db
def test_create_code_hotp(active_user_with_email_otp):
    email_method = active_user_with_email_otp.mfa_methods.get()
    handler = get_mfa_handler(mfa_method=email_method)
    valid_code = handler.create_code()

    assert handler.validate_code(code="123456") is False
    assert handler.validate_code(code=valid_code) is True
    
    # both codes are valid during the validitiy window
    new_valid_code = handler.create_code()
    assert handler.validate_code(code=valid_code) is True
    assert handler.validate_code(code=new_valid_code) is True


@pytest.mark.django_db
def test_validate_code_totp(active_user_with_email_otp):
    email_method = active_user_with_email_otp.mfa_methods.get()
    handler = get_mfa_handler(mfa_method=email_method)
    valid_code = handler.create_code()

    assert handler.validate_code(code="123456") is False
    assert handler.validate_code(code=valid_code) is True
    

@pytest.mark.django_db
def test_validate_code_hotp(active_user_with_email_hotp):
    email_method = active_user_with_email_hotp.mfa_methods.get()
    handler = get_mfa_handler(mfa_method=email_method)
    valid_code = handler.create_code()

    email_method.refresh_from_db()
    assert email_method.code_generated_at is not None

    assert handler.validate_code(code="123456") is False
    email_method.refresh_from_db()
    assert email_method.code_generated_at is not None
    
    # successful validation clears code generation timestemp
    assert handler.validate_code(code=valid_code) is True
    email_method.refresh_from_db()
    assert email_method.code_generated_at is None
    
    # subsequently validating the same code twice fails
    assert handler.validate_code(code=valid_code) is False

    # creating a new code invalidates the previous one
    valid_code = handler.create_code()
    new_valid_code = handler.create_code()
    assert new_valid_code != valid_code
    assert handler.validate_code(code=valid_code) is False
    assert handler.validate_code(code=new_valid_code) is True


@pytest.mark.django_db
def test_validate_code_yubikey(active_user_with_many_otp_methods):
    active_user, _ = active_user_with_many_otp_methods
    yubi_method = active_user.mfa_methods.get(name="yubi")
    handler = get_mfa_handler(mfa_method=yubi_method)
    assert handler.validate_code("t" * 44) is False
