from typing import Any, Dict

from trench.backends.base import AbstractMessageDispatcher
from trench.utils import create_qr_link


class ApplicationBackend(AbstractMessageDispatcher):
    _FIELD_QR_LINK = "qr_link"

    def dispatch_message(self) -> Dict[str, Any]:
        return {self._FIELD_QR_LINK: create_qr_link(self.obj.secret, self.user)}
