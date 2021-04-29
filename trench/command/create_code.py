from pyotp import TOTP
from typing import Optional

from trench.settings import trench_settings


class CreateCodeCommand:
    @staticmethod
    def execute(secret: str) -> str:
        return TOTP(secret, interval=1).now()


create_code_command = CreateCodeCommand.execute
