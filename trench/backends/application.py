from django.contrib.auth.models import User

import logging
from pyotp import TOTP

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import trench_settings


class ApplicationMessageDispatcher(AbstractMessageDispatcher):
    def dispatch_message(self) -> DispatchResponse:
        try:
            qr_link = self._create_qr_link(
                self._mfa_method.secret, self._mfa_method.user
            )
            return SuccessfulDispatchResponse(details=qr_link)
        except Exception as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=str(cause))

    @staticmethod
    def _create_qr_link(secret: str, user: User) -> str:
        return TOTP(secret, interval=1).provisioning_uri(
            getattr(user, User.USERNAME_FIELD),
            trench_settings.APPLICATION_ISSUER_NAME,
        )
