from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

from rest_framework.serializers import ValidationError
from typing import Iterable


class MissingConfigurationError(ImproperlyConfigured):
    def __init__(self, attribute_name: str) -> None:
        super().__init__(f"Could not retrieve attribute '{attribute_name}'.")


class RestrictedCharInBackupCodeError(ImproperlyConfigured):
    def __init__(self, attribute_name: str, restricted_chars: Iterable[str]) -> None:
        super().__init__(
            f"Cannot use any of: {''.join(restricted_chars)} as a character "
            f"for {attribute_name}."
        )


class MethodHandlerMissingError(ImproperlyConfigured):
    def __init__(self, method_name: str) -> None:
        super().__init__(f"Missing handler in {method_name} configuration.")


class MFAValidationError(ValidationError):
    def __str__(self) -> str:
        return ", ".join(detail for detail in self.detail)


class CodeInvalidOrExpiredError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Code invalid or expired."),
            code="code_invalid_or_expired",
        )


class OTPCodeMissingError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("OTP code not provided."), code="otp_code_missing")


class MFAMethodDoesNotExistError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Requested MFA method does not exist."),
            code="mfa_method_does_not_exist",
        )


class MFAMethodNotRegisteredForUserError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_(
                "Selected new primary MFA method is not registered for current user."
            ),
            code="method_not_registered_for_user",
        )


class MFAPrimaryMethodInactiveError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("MFA Method selected as new primary method is not active"),
            code="new_primary_method_inactive",
        )


class MFAMethodAlreadyActiveError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("MFA method already active."),
            code="method_already_active",
        )


class MFANewPrimarySameAsOldError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_(
                "MFA Method to be deactivated cannot be chosen as new "
                "primary method."
            ),
            code="new_primary_same_as_old",
        )


class DeactivationOfPrimaryMFAMethodError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_(
                "Deactivation of MFA method that is set as primary is not allowed."
            ),
            code="deactivation_of_primary",
        )


class MFANotEnabledError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("2FA is not enabled."), code="not_enabled")


class InvalidTokenError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("Invalid or expired token."), code="invalid_token")


class InvalidCodeError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("Invalid or expired code."), code="invalid_code")


class RequiredFieldMissingError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Required field not provided"),
            code="required_field_missing",
        )


class RequiredFieldUpdateFailedError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Failed to update required User data. Try again."),
            code="required_field_update_failed",
        )


class UserAccountDisabledError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("User account is disabled."), code="user_account_disabled"
        )


class UnauthenticatedError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Unable to login with provided credentials."),
            code="unauthenticated",
        )
