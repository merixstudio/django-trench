from typing import Optional, List, Tuple

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import FieldDoesNotExist
from django.utils.crypto import (
    constant_time_compare,
    get_random_string,
    salted_hmac,
)
from django.utils.http import base36_to_int, int_to_base36

import pyotp
from datetime import datetime

from trench.backends.base import AbstractMessageDispatcher
from trench.models import MFAMethod
from trench.settings import api_settings


User = get_user_model()


class UserTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator:
        - user pk in token
        - expires after 15 minutes
        - longer hash (40 instead of 20)
    """

    key_salt = "django.contrib.auth.tokens.PasswordResetTokenGenerator"
    secret = settings.SECRET_KEY

    def make_token(self, user: User) -> str:
        return self._make_token_with_timestamp(user, int(datetime.now().timestamp()))

    def check_token(self, user: User, token: str) -> Optional[User]:
        if not token:
            return None

        try:
            token = str(token)
            user_pk, ts_b36, token_hash = token.rsplit("-", 2)
            ts = base36_to_int(ts_b36)
            user = User._default_manager.get(pk=user_pk)
        except (ValueError, TypeError, User.DoesNotExist):
            return None

        if (datetime.now().timestamp() - ts) > (60 * 15):
            return None  # pragma: no cover

        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return None

        return user

    def _make_token_with_timestamp(self, user: User, timestamp: int, **kwargs) -> str:
        ts_b36 = int_to_base36(timestamp)
        token_hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(user, timestamp),
            secret=self.secret,
        ).hexdigest()
        return "%s-%s-%s" % (user.pk, ts_b36, token_hash)


user_token_generator = UserTokenGenerator()


def create_secret():
    """
    Creates new random secret.

    :returns: Random secret
    :rtype: str
    """
    return pyotp.random_base32(length=api_settings.SECRET_KEY_LENGTH)


def create_otp_code(secret):
    """
    Creates new OTP code.

    :param secret: Secret used to generate OTP
    :type secret: str

    :returns: OTP code
    :rtype: str
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


def create_qr_link(secret: str, user: User) -> str:
    """
    Creates QR link to set application OTP.

    :param secret: Secret used to generate OTP
    :type secret: str
    :param user: User that link should be created for
    :type user: User

    :returns: Link to generate QR code from
    :rtype: str
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        getattr(user, User.USERNAME_FIELD),
        api_settings.APPLICATION_ISSUER_NAME,
    )


def generate_backup_codes(
    quantity: int = api_settings.BACKUP_CODES_QUANTITY,
    length: int = api_settings.BACKUP_CODES_LENGTH,
    allowed_chars: str = api_settings.BACKUP_CODES_CHARACTERS,
) -> List[str]:
    """
    Generates random encrypted backup codes.

    :param quantity: How many codes should be generated
    :type quantity: int
    :param length: How long codes should be
    :type length: int
    :param allowed_chars: Characters to create backup codes from
    :type allowed_chars: str

    :returns: Encrypted backup codes
    :rtype: list[str]
    """
    return [get_random_string(length, allowed_chars) for _ in range(quantity)]


def validate_code(code: str, mfa_method: MFAMethod) -> bool:
    """
    Validates MFA code

    :param code: Code to be validated
    :type code: str
    :param mfa_method: MFA Method to be used to validate the code
    :type mfa_method: MFAMethod

    :returns: True if code is valid, False otherwise
    :rtype: bool
    """
    handler = get_mfa_handler(mfa_method)
    return handler.validate_code(code)


def get_mfa_handler(mfa_method: MFAMethod) -> AbstractMessageDispatcher:
    """
    Provides MFA handler

    :param mfa_method: MFA Method object to be used to retrieve the handler
    :type mfa_method: MFAMethod

    :returns: MFA handler
    :rtype: AbstractMessageDispatcher
    """
    conf = api_settings.MFA_METHODS[mfa_method.name]
    return conf["HANDLER"](
        user=mfa_method.user,
        obj=mfa_method,
        conf=conf,
    )


def get_mfa_model():
    return apps.get_model(api_settings.USER_MFA_MODEL)


def parse_dotted_path(path: str) -> Tuple[Optional[str], str]:
    """
    Extracts attribute name from dotted path.
    """
    try:
        objects, attr = path.rsplit(".", 1)
    except ValueError:
        objects = None
        attr = path

    return objects, attr


def get_innermost_object(obj: object, dotted_path: str = None) -> object:
    """
    For given object return innermost object.
    """
    if not dotted_path:
        return obj
    for o in dotted_path.split("."):
        obj = getattr(obj, o)
    return obj  # pragma: no cover


def get_nested_attr(obj: object, path: str):
    """
    For attribute in dotted path notation retrieves its
    value, name, and field class.
    """
    objects, attr = parse_dotted_path(path)
    try:
        _obj = get_innermost_object(obj, objects)
    except AttributeError:  # pragma: no cover
        return None, None, None  # pragma: no cover

    try:
        field = _obj._meta.get_field(attr)
    except FieldDoesNotExist:  # pragma: no cover
        return None, None, None  # pragma: no cover

    return (
        field.value_from_object(_obj),
        field.get_attname(),
        field.__class__,
    )


def set_nested_attr(obj, path, value):
    """
    Sets value on attribute specified by path.
    Raises AttributeError, DatabaseError
    """
    objects, attr = parse_dotted_path(path)
    _obj = get_innermost_object(obj, objects)
    setattr(_obj, attr, value)
    _obj.save(update_fields=[attr])


def get_nested_attr_value(obj, path):
    objects, attr = parse_dotted_path(path)

    try:
        _obj = get_innermost_object(obj, objects)
    except AttributeError:  # pragma: no cover
        return None  # pragma: no cover

    return getattr(_obj, attr)


def validate_backup_code(value, backup_codes):
    """
    Validates provided code against list of hashed backup codes.
    Returns correct code.

    :param value:
    :param backup_codes:
    :return:
    """
    if api_settings.ENCRYPT_BACKUP_CODES:
        validated_codes = [_ for _ in backup_codes if check_password(value, _)]
    else:  # pragma: no cover
        validated_codes = [_ for _ in backup_codes if value in backup_codes]

    if validated_codes:
        return validated_codes[0]
