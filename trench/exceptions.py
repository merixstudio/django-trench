from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext as _

from rest_framework.exceptions import ValidationError
from typing import Iterable


class BaseMFAException(Exception):
    pass


class MissingSourceFieldAttribute(BaseMFAException):
    def __init__(self, attribute_name: str):
        super().__init__(f"Could not retrieve attribute '{attribute_name}' for given user.")


class InvalidSettingError(ImproperlyConfigured):
    def __init__(self, attribute_name: str):
        super().__init__(f"Invalid API setting: {attribute_name}")


class RestrictedCharInBackupCodeError(ImproperlyConfigured):
    def __init__(self, attribute_name: str, restricted_chars: Iterable[str]):
        super().__init__(
            f"Cannot use any of: {''.join(restricted_chars)} as a character "
            f"for {attribute_name}."
        )


class MethodHandlerMissingError(ImproperlyConfigured):
    def __init__(self, method_name: str):
        super().__init__(f"Missing handler in {method_name} configuration.")


class CodeInvalidOrExpiredValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("Code invalid or expired."),
            code="code_invalid_or_expired",
        )


class OTPCodeMissingValidationError(ValidationError):
    def __init__(self):
        super().__init__(detail=_("OTP code not provided."), code="otp_code_missing")


class MFAMethodDoesNotExistValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("Requested MFA method does not exist."),
            code="mfa_method_does_not_exist",
        )


class MFAMethodNotRegisteredForUserValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_(
                "Selected new primary MFA method is not registered for current user."
            ),
            code="method_not_registered_for_user",
        )


class MFAPrimaryMethodInactiveValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("MFA Method selected as new primary method is not active"),
            code="new_primary_method_inactive",
        )


class MFANewPrimarySameAsOldValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_(
                "MFA Method to be deactivated cannot be chosen as new "
                "primary method."
            ),
            code="new_primary_same_as_old",
        )


class MFANotEnabledValidationError(ValidationError):
    def __init__(self):
        super().__init__(detail=_("2FA is not enabled."), code="not_enabled")


class InvalidTokenValidationError(ValidationError):
    def __init__(self):
        super().__init__(detail=_("Invalid or expired token."), code="invalid_token")


class InvalidCodeValidationError(ValidationError):
    def __init__(self):
        super().__init__(detail=_("Invalid or expired code."), code="invalid_code")


class RequiredFieldMissingValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("Required field not provided"),
            code="required_field_missing",
        )


class RequiredFieldUpdateFailedValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("Failed to update required User data. Try again."),
            code="required_field_update_failed",
        )


class UserAccountDisabledValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("User account is disabled."), code="user_account_disabled"
        )


class UnauthenticatedValidationError(ValidationError):
    def __init__(self):
        super().__init__(
            detail=_("Unable to login with provided credentials."),
            code="unauthenticated",
        )
