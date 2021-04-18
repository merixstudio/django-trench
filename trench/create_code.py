from pyotp import TOTP


class CreateCodeCommand:
    @staticmethod
    def execute(secret: str) -> str:
        return TOTP(secret).now()


create_code_command = CreateCodeCommand.execute
