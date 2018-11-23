from django.utils.translation import ugettext_lazy as _

from templated_mail.mail import BaseEmailMessage

from trench.backends import AbstractMessageDispatcher
from trench.settings import api_settings


class TemplatedMailBackend(AbstractMessageDispatcher):
    EMAIL_SUBJECT = _('Your verification code')

    def dispatch_message(self, *args, **kwargs):
        """
        Sends an email with verification code.
        :return:
        """

        code = self.create_code()

        BaseEmailMessage(
            context={
                'subject': self.EMAIL_SUBJECT,
                'text_body': code,
                'html_body': code,
            },
            template_name='email.html',
        ).send(
            to=[self.to],
            from_email=api_settings.FROM_EMAIL,
        )
        return {'message': _('Email message with MFA code had been sent.')}
