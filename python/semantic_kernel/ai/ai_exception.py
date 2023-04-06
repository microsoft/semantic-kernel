# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Optional


class AIException(Exception):
    class ErrorCodes(Enum):
        # Unknown error.
        UnknownError = -1
        # No response.
        NoResponse = 0
        # Access is denied.
        AccessDenied = 1
        # The request was invalid.
        InvalidRequest = 2
        # The content of the response was invalid.
        InvalidResponseContent = 3
        # The request was throttled.
        Throttling = 4
        # The request timed out.
        RequestTimeout = 5
        # There was an error in the service.
        ServiceError = 6
        # The requested model is not available.
        ModelNotAvailable = 7
        # The supplied configuration was invalid.
        InvalidConfiguration = 8
        # The function is not supported.
        FunctionTypeNotSupported = 9

    # The error code.
    _error_code: ErrorCodes

    def __init__(
        self,
        error_code: ErrorCodes,
        message: str,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """Initializes a new instance of the AIException class.

        Arguments:
            error_code {ErrorCodes} -- The error code.
            message {str} -- The error message.
            inner_exception {Exception} -- The inner exception.
        """
        super().__init__(error_code, message, inner_exception)
        self._error_code = error_code

    @property
    def error_code(self) -> ErrorCodes:
        """Gets the error code.

        Returns:
            ErrorCodes -- The error code.
        """
        return self._error_code
