from django.utils.translation import gettext_lazy as _

import logging
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import TWILIO_VERIFIED_FROM_NUMBER
from twilio.twiml.voice_response import VoiceResponse


class TwilioSMSMessageDispatcher(AbstractMessageDispatcher):
    _SMS_BODY = _("Your verification code is: ")
    _SUCCESS_DETAILS = _("SMS message with MFA code has been sent.")

    def dispatch_message(self) -> DispatchResponse:
        try:
            client = Client()
            client.messages.create(
                body=self._SMS_BODY + self.create_code(),
                to=self._to,
                from_=self._config.get(TWILIO_VERIFIED_FROM_NUMBER),
            )
            return SuccessfulDispatchResponse(details=self._SUCCESS_DETAILS)
        except TwilioRestException as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=cause.msg)


class TwilioCallMessageDispatcher(AbstractMessageDispatcher):
    _CALL_MESSAGE = _("Your verification code is: ")
    _SUCCESS_DETAILS = _("Pick up phone and get key.")

    def dispatch_message(self) -> DispatchResponse:
        try:
            response = VoiceResponse()
            response.say(self._CALL_MESSAGE + self.create_code())
            client = Client()
            client.calls.create(
                twiml=str(response),
                to=self._to,
                from_=self._config.get(TWILIO_VERIFIED_FROM_NUMBER),
            )
            return SuccessfulDispatchResponse(details=self._SUCCESS_DETAILS)
        except TwilioRestException as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=cause.msg)
