from django.utils.translation import gettext_lazy as _
from yubico_client import Yubico
from yubico_client.otp import OTP
from yubico_client.yubico_exceptions import YubicoError

from trench.backends import AbstractMessageDispatcher


class YubiKeyBackend(AbstractMessageDispatcher):
    SMS_BODY = _('Your verification code is: ')

    def dispatch_message(self):
        """
        Do nothing.
        """

        return {'message': _('Generate code using YubiKey')}  # pragma: no cover # noqa

    def activate_mfa(self, code):
        otp = OTP(code)
        if self._validate_yubikey_otp(code=code):
            self.obj.secret = otp.device_id
            self.obj.save(update_fields=['secret'])
            return True
        return False

    def _validate_yubikey_otp(self, code):
        client = Yubico(self.conf['YUBICLOUD_CLIENT_ID'])

        try:
            return client.verify(code, timestamp=True)

        except (YubicoError, Exception):
            return False

    def validate_code(self, code, valid_window):
        if not self._validate_yubikey_otp(code):
            return False
        otp = OTP(code)
        if not self.obj.secret or self.obj.secret != otp.device_id:
            return False
        return True
