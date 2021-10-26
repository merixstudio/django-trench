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
from trench.settings import EMAIL_HTML_TEMPLATE, EMAIL_PLAIN_TEMPLATE, EMAIL_SUBJECT


class SendMailMessageDispatcher(AbstractMessageDispatcher):
    _KEY_MESSAGE = "message"
    _SUCCESS_DETAILS = _("Email message with MFA code has been sent.")

    def dispatch_message(self) -> DispatchResponse:
        context = {"code": self.create_code()}
        email_plain_template = self._config[EMAIL_PLAIN_TEMPLATE]
        email_html_template = self._config[EMAIL_HTML_TEMPLATE]
        try:
            send_mail(
                subject=self._config.get(EMAIL_SUBJECT),
                message=get_template(email_plain_template).render(context),
                html_message=get_template(email_html_template).render(context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=(self._to,),
                fail_silently=False,
            )
            return SuccessfulDispatchResponse(details=self._SUCCESS_DETAILS)
        except SMTPException as cause:  # pragma: nocover
            logging.error(cause, exc_info=True)  # pragma: nocover
            return FailedDispatchResponse(details=str(cause))  # pragma: nocover
