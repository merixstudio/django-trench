from typing import Union

from django_stubs_ext import StrOrPromise
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from trench.exceptions import MFAValidationError


class DispatchResponse(Response):
    _FIELD_DETAILS = "details"


class SuccessfulDispatchResponse(DispatchResponse):
    def __init__(
        self, details: StrOrPromise, status: int = HTTP_200_OK, *args, **kwargs
    ) -> None:
        super().__init__({self._FIELD_DETAILS: details}, status, *args, **kwargs)


class FailedDispatchResponse(DispatchResponse):
    def __init__(
        self,
        details: StrOrPromise,
        status: int = HTTP_422_UNPROCESSABLE_ENTITY,
        *args,
        **kwargs
    ) -> None:
        super().__init__({self._FIELD_DETAILS: details}, status, *args, **kwargs)


class ErrorResponse(Response):
    _FIELD_ERROR = "error"

    def __init__(
        self,
        error: Union[StrOrPromise, MFAValidationError],
        status: int = HTTP_400_BAD_REQUEST,
        *args,
        **kwargs
    ) -> None:
        super().__init__({self._FIELD_ERROR: str(error)}, status, *args, **kwargs)
