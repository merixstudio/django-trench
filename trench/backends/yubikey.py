from django.utils.translation import gettext_lazy as _

import logging
from yubico_client import Yubico
from yubico_client.otp import OTP
from yubico_client.yubico_exceptions import YubicoError

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import DispatchResponse, SuccessfulDispatchResponse
from trench.settings import YUBICLOUD_CLIENT_ID


class YubiKeyMessageDispatcher(AbstractMessageDispatcher):
    def dispatch_message(self) -> DispatchResponse:
        return SuccessfulDispatchResponse(details=_("Generate code using YubiKey"))

    def confirm_activation(self, code: str) -> None:
        self._mfa_method.secret = OTP(code).device_id
        self._mfa_method.save(update_fields=("secret",))

    def validate_confirmation_code(self, code) -> bool:
        """
        The `device_id` is not stored in db yet.
        After successful confirmation `validate_code` should be used.
        """
        return self._validate_yubikey_otp(code)

    def validate_code(self, code: str) -> bool:
        if (
            not self._mfa_method.secret
            or self._mfa_method.secret != OTP(code).device_id
        ):
            return False
        return self._validate_yubikey_otp(code)

    def _validate_yubikey_otp(self, code: str) -> bool:
        try:
            return Yubico(self._config[YUBICLOUD_CLIENT_ID]).verify(
                code, timestamp=True
            )
        except (YubicoError, Exception) as cause:
            logging.error(cause, exc_info=True)
            return False
