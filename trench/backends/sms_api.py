from dataclasses import dataclass

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
from trench.settings import SMSAPI_ACCESS_TOKEN, SMSAPI_FROM_NUMBER, MFAMethodConfig


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


@dataclass(frozen=True)
class MFAMethodConfigSMSAPI(MFAMethodConfig):
    verbose_name = _("sms_api")
    validity_period = 30
    handler = "trench.backends.sms_api.SMSAPIMessageDispatcher"
    source_field = "phone_number"
    smsapi_access_token: str = ""
    smsapi_from_number: str = ""
