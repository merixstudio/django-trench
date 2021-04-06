from django.core.exceptions import ImproperlyConfigured

from typing import Iterable


class BaseMFAException(Exception):
    pass


class MFADoesNotExist(BaseMFAException):
    """User does not have MFA set up"""

    pass


class MFAAlreadyExist(BaseMFAException):
    """User already have MFA set up"""

    pass


class InvalidOTPCode(BaseMFAException):
    """Provided OTP code is not valid"""

    pass


class MethodNotAllowed(BaseMFAException):
    """Given MFA method is not allowed"""

    pass


class MissingSourceFieldAttribute(BaseMFAException):
    def __init__(self, attribute_name: str):
        super(f"Could not retrieve attribute '{attribute_name}' for given user.")


class InvalidSettingError(ImproperlyConfigured):
    def __init__(self, attribute_name: str):
        super(f"Invalid API setting: {attribute_name}")


class RestrictedCharInBackupCodeError(ImproperlyConfigured):
    def __init__(self, attribute_name: str, restricted_chars: Iterable[str]):
        super(
            f"Cannot use any of: {''.join(restricted_chars)} as a character "
            f"for {attribute_name}."
        )


class MethodHandlerMissingError(ImproperlyConfigured):
    def __init__(self, method_name: str):
        super(f"Missing handler in {method_name} configuration.")
