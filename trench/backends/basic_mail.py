from smtplib import SMTPException

from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _

from trench.backends import AbstractMessageDispatcher
from trench.settings import api_settings


class SendMailBackend(AbstractMessageDispatcher):
    EMAIL_SUBJECT = _('Your verification code')

    def dispatch_message(self, *args, **kwargs):
        """
        Sends an email with verification code.
        :return:
        """

        code = self.create_code()

        try:
            send_mail(
                subject=self.EMAIL_SUBJECT,
                message=code,
                from_email=api_settings.FROM_EMAIL,
                recipient_list=[self.to],
                fail_silently=False,
            )
        except SMTPException:  # pragma: no cover
            return {
                'message': _('Email message with MFA code has not been sent.')
            }  # pragma: no cover

        return {'message': _('Email message with MFA code has been sent.')}
