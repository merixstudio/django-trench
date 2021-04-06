from smtplib import SMTPException
from typing import Any, Dict

from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from trench.backends.base import AbstractMessageDispatcher
from trench.settings import api_settings


class SendMailBackend(AbstractMessageDispatcher):
    _FIELD_EMAIL_PLAIN_TEMPLATE = "EMAIL_PLAIN_TEMPLATE"
    _FIELD_EMAIL_HTML_TEMPLATE = "EMAIL_HTML_TEMPLATE"
    _FIELD_EMAIL_SUBJECT = "EMAIL_SUBJECT"
    _KEY_MESSAGE = "message"
    _KEY_CODE = "code"

    def dispatch_message(self, *args, **kwargs) -> Dict[str, str]:
        """Sends an email with verification code."""

        context = self.get_context()
        plain_message = self.render_template(
            self.conf.get(self._FIELD_EMAIL_PLAIN_TEMPLATE),
            context,
        )
        html_message = self.render_template(
            self.conf.get(self._FIELD_EMAIL_HTML_TEMPLATE),
            context,
        )
        try:
            send_mail(
                subject=self.conf.get(self._FIELD_EMAIL_SUBJECT),
                message=plain_message,
                html_message=html_message,
                from_email=api_settings.FROM_EMAIL,
                recipient_list=[self.to],
                fail_silently=False,
            )
        except SMTPException:  # pragma: no cover
            return {
                self._KEY_MESSAGE: _('Email message with MFA code has not been sent.')
            }  # pragma: no cover
        return {self._KEY_MESSAGE: _('Email message with MFA code has been sent.')}

    def get_context(self) -> Dict[str, Any]:
        return {self._KEY_CODE: self.create_code()}

    @staticmethod
    def render_template(name: str, context: Dict[str, Any]):
        return get_template(name).render(context)
