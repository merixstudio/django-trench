from django.contrib.auth.hashers import check_password

from typing import Any, Set, Type

from trench.exceptions import InvalidCodeError, MFAMethodDoesNotExistError
from trench.models import MFABackupCodes
from trench.settings import TrenchAPISettings, trench_settings
from trench.utils import get_mfa_backup_code_model


class RemoveBackupCodeCommand:
    def __init__(self, mfa_backup_code_model: Type[MFABackupCodes], settings: TrenchAPISettings) -> None:
        self._mfa_backup_code_model = mfa_backup_code_model
        self._settings = settings

    def execute(self, user_id: Any, code: str) -> None:
        serialized_codes = (
            self._mfa_backup_code_model.objects.filter(user_id=user_id)
            .values_list("_values", flat=True)
            .first()
        )
        if serialized_codes is None:
            raise MFAMethodDoesNotExistError()
        codes = MFABackupCodes._BACKUP_CODES_DELIMITER.join(
            self._remove_code_from_set(
                backup_codes=set(
                    serialized_codes.split(MFABackupCodes._BACKUP_CODES_DELIMITER)
                ),
                code=code,
            )
        )
        self._mfa_backup_code_model.objects.filter(user_id=user_id).update(
            _values=codes
        )

    def _remove_code_from_set(self, backup_codes: Set[str], code: str) -> Set[str]:
        if not self._settings.ENCRYPT_BACKUP_CODES:
            backup_codes.remove(code)
            return backup_codes
        for backup_code in backup_codes:
            if check_password(code, backup_code):
                backup_codes.remove(backup_code)
                return backup_codes
        raise InvalidCodeError()


remove_backup_code_command = RemoveBackupCodeCommand(
    mfa_backup_code_model=get_mfa_backup_code_model(),
    settings=trench_settings,
).execute
