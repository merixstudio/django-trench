from smtplib import SMTPException

from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from trench.backends import AbstractMessageDispatcher
from trench.settings import api_settings


class SendMailBackend(AbstractMessageDispatcher):
    def dispatch_message(self, *args, **kwargs):
        """
        Sends an email with verification code.
        :return:
        """

        context = self.get_context()
        plain_message = self.render_template(
            self.conf.get('EMAIL_PLAIN_TEMPLATE'),
            context,
        )
        html_message = self.render_template(
            self.conf.get('EMAIL_HTML_TEMPLATE'),
            context,
        )

        try:
            send_mail(
                subject=self.conf.get('EMAIL_SUBJECT'),
                message=plain_message,
                html_message=html_message,
                from_email=api_settings.FROM_EMAIL,
                recipient_list=[self.to],
                fail_silently=False,
            )
        except SMTPException:  # pragma: no cover
            return {
                'message': _('Email message with MFA code has not been sent.')
            }  # pragma: no cover

        return {'message': _('Email message with MFA code has been sent.')}

    def get_context(self):
        return {
            'code': self.create_code()
        }

    @staticmethod
    def render_template(name, context):
        template = get_template(name)
        return template.render(context)
