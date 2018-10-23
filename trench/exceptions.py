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
