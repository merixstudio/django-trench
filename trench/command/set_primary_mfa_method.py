from django.db.transaction import atomic

from typing import Type

from trench.exceptions import MFAMethodDoesNotExistError, MFAPrimaryMethodInactiveError
from trench.models import MFAMethod
from trench.utils import get_mfa_model


class SetPrimaryMFAMethodCommand:
    def __init__(self, mfa_model: Type[MFAMethod]) -> None:
        self._mfa_model = mfa_model

    @atomic
    def execute(self, user_id: int, name: str) -> None:
        self._mfa_model.objects.filter(user_id=user_id, is_primary=True).update(
            is_primary=False
        )
        if not self._mfa_model.objects.is_active_by_name(user_id=user_id, name=name):
            raise MFAPrimaryMethodInactiveError()
        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=name
        ).update(is_primary=True)
        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()


set_primary_mfa_method_command = SetPrimaryMFAMethodCommand(
    mfa_model=get_mfa_model()
).execute
