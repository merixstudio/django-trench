from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

import logging

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import trench_settings


User: Type[AbstractUser] = get_user_model()


class ApplicationMessageDispatcher(AbstractMessageDispatcher):
    def dispatch_message(self) -> DispatchResponse:
        try:
            qr_link = self._create_qr_link(self._mfa_method.user)
            return SuccessfulDispatchResponse(details=qr_link)
        except Exception as cause:  # pragma: nocover
            logging.error(cause, exc_info=True)  # pragma: nocover
            return FailedDispatchResponse(details=str(cause))  # pragma: nocover

    def _create_qr_link(self, user: AbstractUser) -> str:
        return self._get_otp().provisioning_uri(
            getattr(user, User.USERNAME_FIELD),
            trench_settings.APPLICATION_ISSUER_NAME,
        )
