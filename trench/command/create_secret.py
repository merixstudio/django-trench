from pyotp import random_base32
from typing import Callable

from trench.domain.models import TrenchConfig
from trench.settings import trench_settings


class CreateSecretCommand:
    def __init__(self, generator: Callable, settings: TrenchConfig) -> None:
        self._generator = generator
        self._settings = settings

    def execute(self) -> str:
        return self._generator(length=self._settings.secret_key_length)


create_secret_command = CreateSecretCommand(
    generator=random_base32, settings=trench_settings
).execute
