from abc import abstractmethod
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from trench.backends.base import AbstractMessageDispatcher
from trench.exceptions import CodeInvalidOrExpiredError
from trench.query.get_mfa_method import get_mfa_method
from trench.utils import get_mfa_handler, validate_backup_code


class RequiresMFA(BasePermission):
    _FIELD_CODE = "code"

    @staticmethod
    @abstractmethod
    def _get_validation_method():
        pass

    def has_permission(self, request: Request, view: APIView) -> bool:
        code = request.data.get(self._FIELD_CODE)
        if code is None:
            raise CodeInvalidOrExpiredError

        method_name = view.kwargs["method"]
        user = request.user

        mfa = get_mfa_method(user_id=user.id, name=method_name)

        validated_backup_code = validate_backup_code(
            value=code, backup_codes=mfa.backup_codes
        )

        handler: AbstractMessageDispatcher = get_mfa_handler(mfa)
        validation_method = getattr(handler, self._get_validation_method())
        if validation_method(code):
            return True
        if validated_backup_code:
            # FIXME: move to command
            mfa.remove_backup_code(validated_backup_code)
            return True
        raise CodeInvalidOrExpiredError


class RequiresMFAConfirmationCode(RequiresMFA):
    @staticmethod
    def _get_validation_method():
        # FIXME: replace with enum or constant
        return "validate_confirmation_code"


class RequiresMFACode(RequiresMFA):
    @staticmethod
    def _get_validation_method():
        # FIXME: replace with enum or constant
        return "validate_code"
