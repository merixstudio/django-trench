from typing import Callable, Set, Type

from trench.backends.provider import get_mfa_handler
from trench.command.generate_backup_codes import generate_backup_codes_command
from trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from trench.exceptions import MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.utils import get_mfa_model


class ActivateMFAMethodCommand:
    def __init__(
        self, mfa_model: Type[MFAMethod], backup_codes_generator: Callable
    ) -> None:
        self._mfa_model = mfa_model
        self._backup_codes_generator = backup_codes_generator

    def execute(self, user_id: int, name: str, code: str) -> Set[str]:
        mfa = self._mfa_model.objects.get_by_name(user_id=user_id, name=name)

        get_mfa_handler(mfa).confirm_activation(code)

        rows_affected = self._mfa_model.objects.filter(
            user_id=user_id, name=name
        ).update(
            is_active=True,
            is_primary=not self._mfa_model.objects.exclude(name=name).primary_exists(user_id=user_id),
        )

        if rows_affected < 1:
            raise MFAMethodDoesNotExistError()

        backup_codes = regenerate_backup_codes_for_mfa_method_command(
            user_id=user_id,
            name=name,
        )

        return backup_codes


activate_mfa_method_command = ActivateMFAMethodCommand(
    mfa_model=get_mfa_model(),
    backup_codes_generator=generate_backup_codes_command,
).execute
