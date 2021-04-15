from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

import pyotp
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from trench.exceptions import MFAMethodDoesNotExistError
from trench.settings import SOURCE_FIELD, trench_settings


User = get_user_model()


class UserTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator:
        - user pk in token
        - expires after 15 minutes
        - longer hash (40 instead of 20)
    """

    KEY_SALT = "django.contrib.auth.tokens.PasswordResetTokenGenerator"
    SECRET = settings.SECRET_KEY
    EXPIRY_TIME = 60 * 15

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

        if (datetime.now().timestamp() - ts) > self.EXPIRY_TIME:
            return None  # pragma: no cover

        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return None

        return user

    def _make_token_with_timestamp(self, user: User, timestamp: int, **kwargs) -> str:
        ts_b36 = int_to_base36(timestamp)
        token_hash = salted_hmac(
            self.KEY_SALT,
            self._make_hash_value(user, timestamp),
            secret=self.SECRET,
        ).hexdigest()
        return f"{user.pk}-{ts_b36}-{token_hash}"


user_token_generator = UserTokenGenerator()


def create_secret() -> str:
    """
    Creates new random secret.

    :returns: Random secret
    :rtype: str
    """
    return pyotp.random_base32(length=trench_settings.SECRET_KEY_LENGTH)


def create_otp_code(secret: str) -> str:
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
        trench_settings.APPLICATION_ISSUER_NAME,
    )


def validate_code(code: str, mfa_method) -> bool:
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


def get_mfa_handler(mfa_method):
    """
    Provides MFA handler

    :param mfa_method: MFA Method object to be used to retrieve the handler
    :type mfa_method: MFAMethod

    :returns: MFA handler
    :rtype: AbstractMessageDispatcher
    """
    conf = trench_settings.MFA_METHODS[mfa_method.name]
    dispatcher = conf["HANDLER"]
    return dispatcher(mfa_method=mfa_method, config=conf)


def get_mfa_model():
    return apps.get_model(trench_settings.USER_MFA_MODEL)


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
    if trench_settings.ENCRYPT_BACKUP_CODES:
        validated_codes = [_ for _ in backup_codes if check_password(value, _)]
    else:  # pragma: no cover
        validated_codes = [_ for _ in backup_codes if value in backup_codes]

    if validated_codes:
        return validated_codes[0]


def get_method_config_by_name(name: str) -> Dict[str, Any]:
    try:
        return trench_settings.MFA_METHODS[name]
    except KeyError as cause:
        raise MFAMethodDoesNotExistError from cause


def get_source_field_by_method_name(name: str) -> Optional[str]:
    return get_method_config_by_name(name).get(SOURCE_FIELD)
