from django.contrib.auth.hashers import check_password

from typing import Any, Set, Type

from trench.exceptions import InvalidCodeError, MFAMethodDoesNotExistError
from trench.models import MFAMethod
from trench.settings import TrenchAPISettings, trench_settings
from trench.utils import get_mfa_model


class RemoveBackupCodeCommand:
    def __init__(self, mfa_model: Type[MFAMethod], settings: TrenchAPISettings) -> None:
        self._mfa_model = mfa_model
        self._settings = settings

    def execute(self, user_id: Any, method_name: str, code: str) -> None:
        serialized_codes = (
            self._mfa_model.objects.filter(user_id=user_id, name=method_name)
            .values_list("_backup_codes", flat=True)
            .first()
        )
        if serialized_codes is None:
            raise MFAMethodDoesNotExistError()
        codes = MFAMethod._BACKUP_CODES_DELIMITER.join(
            self._remove_code_from_set(
                backup_codes=set(
                    serialized_codes.split(MFAMethod._BACKUP_CODES_DELIMITER)
                ),
                code=code,
            )
        )
        self._mfa_model.objects.filter(user_id=user_id, name=method_name).update(
            _backup_codes=codes
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
    mfa_model=get_mfa_model(),
    settings=trench_settings,
).execute
