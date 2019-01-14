from django.utils.translation import gettext_lazy as _

from smsapi.client import SmsApiPlClient

from trench.backends import AbstractMessageDispatcher


class SmsAPIBackend(AbstractMessageDispatcher):
    SMS_BODY = _('Your verification code is: ')

    def dispatch_message(self):
        """
        Sends a SMS with verification code.
        """

        code = self.create_code()
        self.send_sms(self.to, code)

        return {
            'message': _('SMS message with MFA code has been sent.')
        }  # pragma: no cover # noqa

    def send_sms(self, user_mobile, code):
        client = self.provider_auth()

        kwargs = {}
        if self.conf.get('SMSAPI_FROM_NUMBER'):
            kwargs['from_'] = self.conf.get(
                'SMSAPI_FROM_NUMBER'
            )  # pragma: no cover

        client.sms.send(
            message=self.SMS_BODY + code,
            to=user_mobile,
            **kwargs
        )

    def provider_auth(self):
        return SmsApiPlClient(
            access_token=self.conf.get('SMSAPI_ACCESS_TOKEN')
        )
