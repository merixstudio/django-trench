from django.contrib.auth.hashers import check_password

from typing import Iterable, Optional

from trench.settings import TrenchAPISettings, trench_settings


class ValidateBackupCodeCommand:
    def __init__(self, settings: TrenchAPISettings) -> None:
        self._settings = settings

    def execute(self, value: str, backup_codes: Iterable) -> Optional[str]:
        if not self._settings.ENCRYPT_BACKUP_CODES:
            return value if value in backup_codes else None
        for backup_code in backup_codes:
            if check_password(value, backup_code):
                return backup_code
        return None


validate_backup_code_command = ValidateBackupCodeCommand(
    settings=trench_settings
).execute
