from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

from trench.command.authenticate_second_factor import authenticate_second_step_command


def mfa_login_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """

    def test(user):
        # return user.is_verified() or (user.is_authenticated and not user_has_device(user))
        return authenticate_second_step_command

    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        # test,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
