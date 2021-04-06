from django.utils.translation import gettext_lazy as _

from yubico_client import Yubico
from yubico_client.otp import OTP
from yubico_client.yubico_exceptions import YubicoError

from trench.backends.base import AbstractMessageDispatcher


class YubiKeyBackend(AbstractMessageDispatcher):
    SMS_BODY = _('Your verification code is: ')

    def dispatch_message(self):
        """
        Do nothing.
        """

        return {'message': _('Generate code using YubiKey')}  # pragma: no cover # noqa

    def confirm_activation(self, code):
        """
        After successful confirmation store `device_id`
        in field `secret` MFAMethod model.
        """

        otp = OTP(code)
        self.obj.secret = otp.device_id
        self.obj.save(update_fields=('secret',))

    def validate_confirmation_code(self, code):
        """
        Different approach to validate `code` in confirmation action because
        `device_id` is not stored in db yet. After successful confirmation,
        in any other case `validate_code` should be used.
        """

        return self._validate_yubikey_otp(code)

    def validate_code(self, code):
        otp = OTP(code)
        if not self.obj.secret or self.obj.secret != otp.device_id:
            return False
        if not self._validate_yubikey_otp(code):
            return False
        return True

    def _validate_yubikey_otp(self, code):
        client = Yubico(self.conf['YUBICLOUD_CLIENT_ID'])
        try:
            return client.verify(code, timestamp=True)
        except (YubicoError, Exception):
            return False
