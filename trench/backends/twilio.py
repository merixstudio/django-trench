from django.conf import settings
from django.utils.translation import gettext_lazy as _

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from trench.backends import AbstractMessageDispatcher


class TwilioBackend(AbstractMessageDispatcher):
    SMS_BODY = _('Your verification code is: ')

    def dispatch_message(self):
        """
        Sends a SMS with verification code.
        :return:
        """
        code = self.create_code()

        if settings.DEBUG:
            try:  # pragma: no cover
                self.send_sms(self.to, code)  # pragma: no cover
            except TwilioRestException as e:  # pragma: no cover
                print(  # pragma: no cover
                    'Error found: {}\n'
                    'SMS to number {}\n'
                    'Your code is {}.'.format(e, self.to, code))
        else:
            self.send_sms(self.to, code)
        return {'message': _('SMS message with MFA code has been sent.')}  # pragma: no cover # noqa

    def send_sms(self, user_mobile, code):
        client = self.provider_auth()
        client.messages.create(  # pragma: no cover
            body=self.SMS_BODY + code,
            to=user_mobile,
            from_=self.conf.get('TWILIO_VERIFIED_FROM_NUMBER')
        )

    def provider_auth(self):
        return Client(
            self.conf.get('TWILIO_ACCOUNT_SID'),
            self.conf.get('TWILIO_AUTH_TOKEN'),
        )
