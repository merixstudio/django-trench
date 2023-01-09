from django.db.models import Model

from abc import ABC, abstractmethod
from pyotp import TOTP
from typing import Any, Dict, Optional, Tuple
from django.utils import timezone
from trench.command.create_otp import create_otp_command
from trench.exceptions import MissingConfigurationError
from trench.models import MFAMethod
from trench.responses import DispatchResponse
from trench.settings import SOURCE_FIELD, VALIDITY_PERIOD, ALLOW_REUSE_CODE, trench_settings
from trench.utils import get_mfa_used_code_model


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
        user = self._mfa_method.user
        method_name = self._mfa_method.name

        valid_code = self._get_otp().verify(otp=code)
        if not valid_code:
            return False

        mfa_used_code_model = get_mfa_used_code_model()
        threshold = timezone.now() + timezone.timedelta(seconds=self._get_valid_window())

        used_code_exist = mfa_used_code_model.objects.filter(user=user, code=code, method=method_name, expires_at__gt=timezone.now()).exists()

        mfa_used_code_model.objects.create(
            user=user,
            code=code,
            method=method_name,
            expires_at=threshold
        )

        if used_code_exist and not self._get_allow_reuse_code():
            return False

        return valid_code

    def _get_otp(self) -> TOTP:
        return create_otp_command(
            secret=self._mfa_method.secret, interval=self._get_valid_window()
        )

    def _get_valid_window(self) -> int:
        return self._config.get(
            VALIDITY_PERIOD, trench_settings.DEFAULT_VALIDITY_PERIOD
        )

    def _get_allow_reuse_code(self) -> bool:
        user_settings = trench_settings.user_settings
        if "ALLOW_REUSE_CODE" not in user_settings:
            return trench_settings.ALLOW_REUSE_CODE

        return user_settings["ALLOW_REUSE_CODE"]
