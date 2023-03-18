from django.contrib.auth import authenticate
from django.contrib.auth.base_user import AbstractBaseUser
from rest_framework.request import Request

from trench.exceptions import UnauthenticatedError


class AuthenticateUserCommand:
    @staticmethod
    def execute(request: Request, username: str, password: str) -> AbstractBaseUser:
        user = authenticate(
            request=request,
            username=username,
            password=password,
        )
        if user is None:
            raise UnauthenticatedError()
        return user


authenticate_user_command = AuthenticateUserCommand.execute
