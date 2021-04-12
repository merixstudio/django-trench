from django.db.transaction import atomic

from typing_extensions import Type

from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.query.is_mfa_method_active import is_mfa_method_active_query
from trench.utils import get_mfa_model


class SetPrimaryMFAMethodCommand:
    def __init__(self, mfa_model: Type[MFAMethod]):
        self._mfa_model = mfa_model

    @atomic
    def execute(self, user_id: int, name: str):
        self._mfa_model.objects.filter(user_id=user_id, is_primary=True).update(
            is_primary=False
        )
        is_mfa_method_active_query(user_id=user_id, name=name)
        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=name
        ).update(is_primary=True)
        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()


set_primary_mfa_method_command = SetPrimaryMFAMethodCommand(
    mfa_model=get_mfa_model()
).execute
