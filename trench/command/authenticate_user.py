from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework.request import Request

from trench.exceptions import UnauthenticatedError


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
        return user


authenticate_user_command = AuthenticateUserCommand.execute
