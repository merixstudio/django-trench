from django.db.models import Model
from django.utils import timezone

from abc import ABC, abstractmethod
from datetime import timedelta
from pyotp import TOTP, HOTP
from typing import Any, Dict, Optional, Tuple

from trench.command.create_otp import create_totp_command, create_hotp_command
from trench.exceptions import MissingConfigurationError
from trench.models import MFAMethod
from trench.responses import DispatchResponse
from trench.settings import SOURCE_FIELD, VALIDITY_PERIOD, trench_settings


class AbstractMessageDispatcher(ABC):
    def __init__(self, mfa_method: MFAMethod, config: Dict[str, Any]) -> None:
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

    def _get_nested_attr_value(self, obj: Model, path: str) -> Optional[str]:
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
    def _get_innermost_object(obj: Model, dotted_path: Optional[str] = None) -> Model:
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
        raise NotImplementedError  # pragma: no cover

    def create_code(self) -> str:
        return self._get_otp().now()

    def confirm_activation(self, code: str) -> None:
        pass

    def validate_confirmation_code(self, code: str) -> bool:
        return self.validate_code(code)

    def validate_code(self, code: str) -> bool:
        return self._get_otp().verify(otp=code)

    def _get_otp(self) -> TOTP:
        return create_totp_command(
            secret=self._mfa_method.secret, interval=self._get_valid_window()
        )

    def _get_valid_window(self) -> int:
        return self._config.get(
            VALIDITY_PERIOD, trench_settings.DEFAULT_VALIDITY_PERIOD
        )


class AbstractHotpMessageDispatcher(AbstractMessageDispatcher):
    def create_code(self) -> str:
        self._mfa_method.counter += 1
        self._mfa_method.code_generated_at = timezone.now()
        self._mfa_method.save()
        return self._get_otp().at(self._mfa_method.counter)

    def validate_code(self, code: str) -> bool:
        if not self._mfa_method.code_generated_at:
            return False

        is_valid = self._get_otp().verify(otp=code, counter=self._mfa_method.counter)
        if not is_valid:
            return False

        min_time = self._mfa_method.code_generated_at
        max_time = self._mfa_method.code_generated_at + timedelta(
            seconds=self._get_valid_window()
        )
        now = timezone.now()
        if now < min_time or now > max_time:
            return False

        self._mfa_method.code_generated_at = None
        self._mfa_method.save()
        return True

    def _get_otp(self) -> HOTP:
        return create_hotp_command(secret=self._mfa_method.secret)
