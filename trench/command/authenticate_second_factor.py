from django.contrib.auth.models import User

from trench.backends.provider import get_mfa_handler
from trench.command.validate_backup_code import validate_backup_code_command
from trench.exceptions import InvalidCodeError, InvalidTokenError
from trench.query.list_active_mfa_methods import list_active_mfa_methods_query
from trench.utils import user_token_generator


class AuthenticateSecondFactorCommand:
    @classmethod
    def execute(cls, code: str, ephemeral_token: str) -> User:
        user = user_token_generator.check_token(user=None, token=ephemeral_token)
        if user is None:
            raise InvalidTokenError()
        cls.is_authenticated(user_id=user.id, code=code)
        return user

    @classmethod
    def is_authenticated(cls, user_id: int, code: str):
        for auth_method in list_active_mfa_methods_query(user_id=user_id):
            validated_backup_code = validate_backup_code_command(
                value=code, backup_codes=auth_method.backup_codes
            )
            if get_mfa_handler(mfa_method=auth_method).validate_code(code=code):
                return
            if validated_backup_code:
                auth_method.remove_backup_code(validated_backup_code)
                return
        raise InvalidCodeError()


authenticate_second_step_command = AuthenticateSecondFactorCommand.execute
