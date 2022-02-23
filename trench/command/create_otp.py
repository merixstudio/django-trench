from pyotp import TOTP


class CreateOTPCommand:
    @staticmethod
    def execute(secret: str, interval: int) -> TOTP:
        return TOTP(secret, interval=interval)


create_otp_command = CreateOTPCommand.execute
