import pyotp
from abc import abstractmethod
from typing import Any, Dict

from trench.exceptions import MissingSourceFieldAttribute
from trench.settings import api_settings
from trench.utils import create_otp_code, get_nested_attr_value


class AbstractMessageDispatcher:
    _FIELD_SOURCE_FIELD = "SOURCE_FIELD"
    _FIELD_VALIDITY_PERIOD = "VALIDITY_PERIOD"

    def __init__(self, user, obj, conf):
        self.user = user
        self.obj = obj
        self.conf = conf
        self.to = ""

        if self._FIELD_SOURCE_FIELD in conf:
            source = get_nested_attr_value(user, conf[self._FIELD_SOURCE_FIELD])
            if source is None:
                raise MissingSourceFieldAttribute(  # pragma: no cover
                    attribute_name=conf[self._FIELD_SOURCE_FIELD]
                )
            self.to = source

    @abstractmethod
    def dispatch_message(self) -> Dict[str, Any]:
        pass  # pragma: no cover

    def create_code(self) -> str:
        return create_otp_code(self.obj.secret)

    def confirm_activation(self, code: str):
        pass

    def validate_confirmation_code(self, code: str) -> bool:
        return self.validate_code(code)

    def validate_code(self, code: str) -> bool:
        validity_period = (
            self.conf.get(self._FIELD_VALIDITY_PERIOD)
            or api_settings.DEFAULT_VALIDITY_PERIOD
        )
        return pyotp.TOTP(self.obj.secret).verify(
            otp=code, valid_window=int(validity_period / 30)
        )
