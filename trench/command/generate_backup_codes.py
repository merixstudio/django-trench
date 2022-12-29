from django.utils.crypto import get_random_string

from typing import Callable, Set

from trench.settings import trench_settings


class GenerateBackupCodesCommand:
    def __init__(self, random_string_generator: Callable) -> None:
        self._random_string_generator = random_string_generator

    def execute(
        self,
    ) -> Set[str]:
        """
        Generates random encrypted backup codes.

        :returns: Encrypted backup codes
        :rtype: set[str]
        """
        return {
            self._random_string_generator(
                trench_settings.backup_codes_length,
                trench_settings.backup_codes_characters
            )
            for _ in range(trench_settings.backup_codes_quantity)
        }


generate_backup_codes_command = GenerateBackupCodesCommand(
    random_string_generator=get_random_string,
).execute
