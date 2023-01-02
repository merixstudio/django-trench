from django.utils.translation import gettext_lazy as _

import logging
from smsapi.client import SmsApiPlClient
from smsapi.exception import SmsApiException

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import SMSAPI_ACCESS_TOKEN, SMSAPI_FROM_NUMBER


class SMSAPIMessageDispatcher(AbstractMessageDispatcher):
    _SMS_BODY = _("Your verification code is: ")
    _SUCCESS_DETAILS = _("SMS message with MFA code has been sent.")

    def dispatch_message(self) -> DispatchResponse:
        try:
            client = SmsApiPlClient(access_token=self._config.get(SMSAPI_ACCESS_TOKEN))
            from_number = self._config.get(SMSAPI_FROM_NUMBER)
            kwargs = {"from_": from_number} if from_number else {}
            client.sms.send(
                message=self._SMS_BODY + self.create_code(),
                to=self._to,
                **kwargs,
            )
            return SuccessfulDispatchResponse(details=self._SUCCESS_DETAILS)
        except SmsApiException as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=cause.message)
