from django.utils.translation import gettext_lazy as _

from trench.backends import AbstractMessageDispatcher


class YubiKeyBackend(AbstractMessageDispatcher):
    SMS_BODY = _('Your verification code is: ')

    def dispatch_message(self):
        """
        Do nothing.
        """

        return {'message': _('Generate code using YubiKey')}  # pragma: no cover # noqa
