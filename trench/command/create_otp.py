from pyotp import TOTP, HOTP


class CreateTOTPCommand:
    @staticmethod
    def execute(secret: str, interval: int) -> TOTP:
        return TOTP(secret, interval=interval)


create_totp_command = CreateTOTPCommand.execute


class CreateHOTPCommand:
    @staticmethod
    def execute(secret: str) -> HOTP:
        return HOTP(secret)


create_hotp_command = CreateHOTPCommand.execute
