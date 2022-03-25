from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from dataclasses import dataclass

import logging

from django.utils.translation import gettext_lazy as _

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import trench_settings, MFAMethodConfig


User: AbstractUser = get_user_model()


class ApplicationMessageDispatcher(AbstractMessageDispatcher):
    def dispatch_message(self) -> DispatchResponse:
        try:
            qr_link = self._create_qr_link(self._mfa_method.user)
            return SuccessfulDispatchResponse(details=qr_link)
        except Exception as cause:  # pragma: nocover
            logging.error(cause, exc_info=True)  # pragma: nocover
            return FailedDispatchResponse(details=str(cause))  # pragma: nocover

    def _create_qr_link(self, user: User) -> str:
        return self._get_otp().provisioning_uri(
            getattr(user, User.USERNAME_FIELD),
            trench_settings.APPLICATION_ISSUER_NAME,
        )


@dataclass(frozen=True)
class MFAMethodConfigApp(MFAMethodConfig):
    verbose_name = _("app")
    validity_period = 30
    handler = "trench.backends.application.ApplicationMessageDispatcher"
    uses_third_party_client: bool = True
