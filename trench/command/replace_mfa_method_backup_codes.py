from django.contrib.auth.hashers import make_password

from typing import Callable, Set, Type

from trench.command.generate_backup_codes import generate_backup_codes_command
from trench.exceptions import MFABackupCodeError
from trench.models import MFABackupCode
from trench.settings import trench_settings
from trench.utils import get_mfa_backup_code_model


class RegenerateBackupCodesForMFAMethodCommand:
    def __init__(
        self,
        requires_encryption: bool,
        mfa_backup_code_model: Type[MFABackupCode],
        code_hasher: Callable,
        codes_generator: Callable,
    ) -> None:
        self._requires_encryption = requires_encryption
        self.mfa_backup_code_model = mfa_backup_code_model
        self._code_hasher = code_hasher
        self._codes_generator = codes_generator

    def execute(self, user_id: int) -> Set[str]:
        backup_codes = self._codes_generator()
        rows_affected = self.mfa_backup_code_model.objects.filter(
            user_id=user_id
        ).update(
            _backup_codes=MFABackupCode._BACKUP_CODES_DELIMITER.join(
                [self._code_hasher(backup_code) for backup_code in backup_codes]
                if self._requires_encryption
                else backup_codes
            ),
        )

        if rows_affected < 1:
            raise MFABackupCodeError()

        return backup_codes


regenerate_backup_codes_for_mfa_method_command = (
    RegenerateBackupCodesForMFAMethodCommand(
        requires_encryption=trench_settings.ENCRYPT_BACKUP_CODES,
        mfa_backup_code_model=get_mfa_backup_code_model(),
        code_hasher=make_password,
        codes_generator=generate_backup_codes_command,
    ).execute
)
