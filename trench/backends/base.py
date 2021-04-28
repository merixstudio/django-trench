from django.db.models import Model

import pyotp
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from trench.command.create_code import create_code_command
from trench.exceptions import MissingConfigurationError
from trench.models import MFAMethod
from trench.responses import DispatchResponse
from trench.settings import SOURCE_FIELD, VALIDITY_PERIOD, trench_settings


class AbstractMessageDispatcher(ABC):
    def __init__(self, mfa_method: MFAMethod, config: Dict[str, Any]):
        self._mfa_method = mfa_method
        self._config = config
        self._to = self._get_source_field()

    def _get_source_field(self) -> Optional[str]:
        if SOURCE_FIELD in self._config:
            source = self._get_nested_attr_value(
                self._mfa_method.user, self._config[SOURCE_FIELD]
            )
            if source is None:
                raise MissingConfigurationError(
                    attribute_name=self._config[SOURCE_FIELD]
                )
            return source
        return None

    def _get_nested_attr_value(self, obj, path) -> Optional[str]:
        objects, attr = self._parse_dotted_path(path)
        try:
            _obj = self._get_innermost_object(obj, objects)
        except AttributeError:  # pragma: no cover
            return None  # pragma: no cover
        return getattr(_obj, attr)

    @staticmethod
    def _parse_dotted_path(path: str) -> Tuple[Optional[str], str]:
        """
        Extracts attribute name from dotted path.
        """
        try:
            objects, attr = path.rsplit(".", 1)
            return objects, attr
        except ValueError:
            return None, path

    @staticmethod
    def _get_innermost_object(obj: Model, dotted_path: str = None) -> Model:
        """
        For given object return innermost object.
        """
        if dotted_path is None:
            return obj
        for o in dotted_path.split("."):
            obj = getattr(obj, o)
        return obj  # pragma: no cover

    @abstractmethod
    def dispatch_message(self) -> DispatchResponse:
        pass

    def create_code(self) -> str:
        return create_code_command(secret=self._mfa_method.secret)

    def confirm_activation(self, code: str):
        pass

    def validate_confirmation_code(self, code: str) -> bool:
        return self.validate_code(code)

    def validate_code(self, code: str) -> bool:
        validity_period = self._config.get(
            VALIDITY_PERIOD, trench_settings.DEFAULT_VALIDITY_PERIOD
        )
        return pyotp.TOTP(self._mfa_method.secret).verify(
            otp=code, valid_window=int(validity_period)
        )
