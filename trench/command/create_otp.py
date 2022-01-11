from pyotp import TOTP
from trench.settings import trench_settings


class CreateOTPCommand:
    @staticmethod
    def execute(secret: str) -> TOTP:
        return TOTP(secret, interval=trench_settings.TOKEN_PERIOD)


create_otp_command = CreateOTPCommand.execute
