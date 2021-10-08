from pyotp import TOTP


class CreateOTPCommand:
    @staticmethod
    def execute(secret: str) -> TOTP:
        return TOTP(secret, interval=1)


create_otp_command = CreateOTPCommand.execute
