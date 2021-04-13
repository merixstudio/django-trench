from django.db.transaction import atomic

from typing_extensions import Type

from trench.exceptions import (
    DeactivationOfPrimaryMFAMethodError,
    MFAMethodDoesNotExistError,
    MFANotEnabledError,
)
from trench.models import MFAMethod
from trench.query.get_mfa_method import get_mfa_method_query
from trench.utils import get_mfa_model


class DeactivateMFAMethodCommand:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    @atomic
    def execute(self, mfa_method_name: str, user_id: int):
        mfa = get_mfa_method_query(user_id=user_id, name=mfa_method_name)
        if mfa.is_primary:
            raise DeactivationOfPrimaryMFAMethodError()
        if not mfa.is_active:
            raise MFANotEnabledError()

        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=mfa_method_name
        ).update(is_active=False)

        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()


deactivate_mfa_method = DeactivateMFAMethodCommand(mfa_model=get_mfa_model()).execute
