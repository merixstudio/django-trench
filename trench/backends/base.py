import pyotp
from abc import abstractmethod
from typing import Any, Dict, Optional

from trench.exceptions import MissingConfigurationError
from trench.models import MFAMethod
from trench.responses import DispatchResponse
from trench.settings import SOURCE_FIELD, VALIDITY_PERIOD, trench_settings
from trench.utils import create_otp_code, get_nested_attr_value


class AbstractMessageDispatcher:
    def __init__(self, mfa_method: MFAMethod, config: Dict[str, Any]):
        self._mfa_method = mfa_method
        self._config = config
        self._to = self._get_source_field()

    def _get_source_field(self) -> Optional[str]:
        if SOURCE_FIELD in self._config:
            source = get_nested_attr_value(
                self._mfa_method.user, self._config[SOURCE_FIELD]
            )
            if source is None:
                raise MissingConfigurationError(
                    attribute_name=self._config[SOURCE_FIELD]
                )
            return source
        return None

    @abstractmethod
    def dispatch_message(self) -> DispatchResponse:
        pass

    def create_code(self) -> str:
        return create_otp_code(self._mfa_method.secret)

    def confirm_activation(self, code: str):
        pass

    def validate_confirmation_code(self, code: str) -> bool:
        return self.validate_code(code)

    def validate_code(self, code: str) -> bool:
        validity_period = self._config.get(
            VALIDITY_PERIOD, trench_settings.DEFAULT_VALIDITY_PERIOD
        )
        return pyotp.TOTP(self._mfa_method.secret).verify(
            otp=code, valid_window=int(validity_period / 30)
        )
