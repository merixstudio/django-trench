from django.contrib.auth import authenticate, get_user_model

from rest_framework.request import Request

from trench.exceptions import UnauthenticatedError, UserAccountDisabledError
from trench.settings import api_settings


User = get_user_model()


class AuthenticateUserCommand:
    @staticmethod
    def execute(request: Request, username: str, password: str) -> User:
        user = authenticate(
            request=request,
            username=username,
            password=password,
        )
        if user is None:
            raise UnauthenticatedError()
        if not getattr(user, api_settings.USER_ACTIVE_FIELD, True):
            raise UserAccountDisabledError()
        return user


authenticate_user_command = AuthenticateUserCommand.execute
