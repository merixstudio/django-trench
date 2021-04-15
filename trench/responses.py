from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_422_UNPROCESSABLE_ENTITY


class DispatchResponse(Response):
    _FIELD_DETAILS = "details"


class SuccessfulDispatchResponse(DispatchResponse):
    def __init__(self, details: str, status: str = HTTP_200_OK, *args, **kwargs):
        super().__init__(
            data={self._FIELD_DETAILS: details}, status=status, *args, **kwargs
        )


class FailedDispatchResponse(DispatchResponse):
    def __init__(
        self, details: str, status: str = HTTP_422_UNPROCESSABLE_ENTITY, *args, **kwargs
    ):
        super().__init__(
            data={self._FIELD_DETAILS: details}, status=status, *args, **kwargs
        )
