from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

import logging
from smtplib import SMTPException

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import EMAIL_HTML_TEMPLATE, EMAIL_PLAIN_TEMPLATE, EMAIL_SUBJECT_TEMPLATE, EMAIL_SUBJECT


class SendMailMessageDispatcher(AbstractMessageDispatcher):
    _KEY_MESSAGE = "message"
    _SUCCESS_DETAILS = _("Email message with MFA code has been sent.")

    def get_context(self, request):
        return {}

    def get_from_email(self, request):
        return settings.DEFAULT_FROM_EMAIL

    def dispatch_message(self) -> DispatchResponse:
        request = self.request
        context = self.get_context(request)
        context.update({"code": self.create_code()})
        email_subject = self._config[EMAIL_SUBJECT]
        email_subject_template = self._config[EMAIL_SUBJECT_TEMPLATE]
        email_plain_template = self._config[EMAIL_PLAIN_TEMPLATE]
        email_html_template = self._config[EMAIL_HTML_TEMPLATE]
        from_email = self.get_from_email(request)
        if not email_subject:
            email_subject = get_template(email_subject_template).render(context).replace('\n','')
        email_plain = get_template(email_plain_template).render(context)
        email_html = get_template(email_html_template).render(context)
        try:
            send_mail(
                subject=email_subject,
                message=email_plain,
                html_message=email_html,
                from_email=from_email,
                recipient_list=(self._to,),
                fail_silently=False,
            )
            return SuccessfulDispatchResponse(details=self._SUCCESS_DETAILS)
        except SMTPException as cause:  # pragma: nocover
            logging.error(cause, exc_info=True)  # pragma: nocover
            return FailedDispatchResponse(details=str(cause))  # pragma: nocover
