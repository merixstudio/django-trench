from pyotp import TOTP
from typing import Optional

from trench.settings import trench_settings


class CreateCodeCommand:
    def __init__(self, default_validity: int):
        self._default_interval = default_validity

    def execute(self, secret: str, interval: Optional[int] = None) -> str:
        return TOTP(secret, interval=interval if interval is not None else self._default_interval).now()


create_code_command = CreateCodeCommand(
    default_validity=trench_settings.DEFAULT_VALIDITY_PERIOD
).execute
