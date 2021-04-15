import logging

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.utils import create_qr_link


class ApplicationMessageDispatcher(AbstractMessageDispatcher):
    def dispatch_message(self) -> DispatchResponse:
        try:
            qr_link = create_qr_link(self._mfa_method.secret, self._mfa_method.user)
            return SuccessfulDispatchResponse(details=qr_link)
        except Exception as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=str(cause))
