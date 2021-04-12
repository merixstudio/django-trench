from typing import Callable, List
from typing_extensions import Type

from trench.command.generate_backup_codes import generate_backup_codes_command
from trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.query.get_mfa_method import get_mfa_method
from trench.query.primary_mfa_method_exists import primary_mfa_method_exists_query
from trench.utils import get_mfa_handler, get_mfa_model


class ActivateMFAMethodCommand:
    def __init__(self, mfa_model: Type[MFAMethod], backup_codes_generator: Callable):
        self._mfa_model = mfa_model
        self._backup_codes_generator = backup_codes_generator

    def execute(self, user_id: int, name: str, code: str) -> List[str]:
        mfa = get_mfa_method(user_id=user_id, name=name)
        handler = get_mfa_handler(mfa)
        handler.confirm_activation(code)

        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=name
        ).update(
            is_active=True,
            is_primary=not primary_mfa_method_exists_query(user_id=user_id),
        )

        backup_codes = regenerate_backup_codes_for_mfa_method_command(
            user_id=user_id,
            name=name,
        )

        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()

        return backup_codes


activate_mfa_method_command = ActivateMFAMethodCommand(
    mfa_model=get_mfa_model(),
    backup_codes_generator=generate_backup_codes_command,
).execute
