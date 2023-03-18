from datetime import datetime
from typing import List, Optional, Tuple, Type

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from django.utils.translation import gettext_lazy as _

from trench.models import MFAMethod
from trench.settings import VERBOSE_NAME, trench_settings


class UserTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator:
        - user pk in token
        - expires after 15 minutes
        - longer hash (40 instead of 20)
    """

    KEY_SALT = "django.contrib.auth.tokens.PasswordResetTokenGenerator"
    SECRET = settings.SECRET_KEY
    EXPIRY_TIME = 60 * 15

    def make_token(self, user: AbstractBaseUser) -> str:
        return self._make_token_with_timestamp(user, int(datetime.now().timestamp()))

    def check_token(  # type: ignore[override] # fixing return type would be a breaking change
        self, user: Optional[AbstractBaseUser], token: Optional[str]
    ) -> Optional[AbstractBaseUser]:
        user_model = get_user_model()
        if not token:
            return None
        try:
            token = str(token)
            user_pk, ts_b36, token_hash = token.rsplit("-", 2)
            ts = base36_to_int(ts_b36)
            token_user = user_model._default_manager.get(pk=user_pk)
        except (ValueError, TypeError, user_model.DoesNotExist):
            return None

        if (datetime.now().timestamp() - ts) > self.EXPIRY_TIME:
            return None  # pragma: no cover

        if not constant_time_compare(
            self._make_token_with_timestamp(token_user, ts), token
        ):
            return None  # pragma: no cover

        return token_user

    def _make_token_with_timestamp(  # type: ignore[override]
        self, user: AbstractBaseUser, timestamp: int, **kwargs
    ) -> str:
        ts_b36 = int_to_base36(timestamp)
        token_hash = salted_hmac(
            self.KEY_SALT,
            self._make_hash_value(user, timestamp),
            secret=self.SECRET,
        ).hexdigest()
        return f"{user.pk}-{ts_b36}-{token_hash}"


user_token_generator = UserTokenGenerator()


def get_mfa_model() -> Type[MFAMethod]:
    return apps.get_model(trench_settings.USER_MFA_MODEL)


def available_method_choices() -> List[Tuple[str, str]]:
    return [
        (method_name, method_config.get(VERBOSE_NAME, _(method_name)))
        for method_name, method_config in trench_settings.MFA_METHODS.items()
    ]
