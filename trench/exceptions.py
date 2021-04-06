from django.core.exceptions import ImproperlyConfigured


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
    """Atrribute specified as required for given backend is missing"""
    pass


class InvalidSettingError(ImproperlyConfigured):
    def __init__(self, attribute_name: str):
        super(f"Invalid API setting: {attribute_name}")


class RestrictedCharInBackupCodeError(ImproperlyConfigured):
    def __init__(self, attribute_name: str):
        super(f"Cannot use comma (,) as a character for {attribute_name}.")


class MethodHandlerMissingError(ImproperlyConfigured):
    def __init__(self, method_name: str):
        super(f"Missing handler in {method_name} configuration.")
