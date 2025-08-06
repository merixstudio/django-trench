from django.utils.translation import gettext_lazy as _

import logging
import boto3
import botocore.exceptions

from trench.backends.base import AbstractMessageDispatcher
from trench.responses import (
    DispatchResponse,
    FailedDispatchResponse,
    SuccessfulDispatchResponse,
)
from trench.settings import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION
from botocore.exceptions import ClientError, EndpointConnectionError

class AWSMessageDispatcher(AbstractMessageDispatcher):
    _SMS_BODY = _("Your verification code is: ")
    _SUCCESS_DETAILS = _("SMS message with MFA code has been sent.")

    def dispatch_message(self) -> DispatchResponse:
        try:
            client = boto3.client(
                "sns",
                aws_access_key_id=self._config.get(AWS_ACCESS_KEY),
                aws_secret_access_key=self._config.get(AWS_SECRET_KEY),
                region_name=self._config.get(AWS_REGION),
            )
            client.publish(
                PhoneNumber=self._to,
                Message=self._SMS_BODY + self.create_code(),
            )
            return SuccessfulDispatchResponse(details=self._SUCCESS_DETAILS)
        except ClientError as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=str(cause))
        except EndpointConnectionError as cause:
            logging.error(cause, exc_info=True)
            return FailedDispatchResponse(details=str(cause))
