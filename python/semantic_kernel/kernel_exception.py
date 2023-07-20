# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Optional


class KernelException(Exception):
    class ErrorCodes(Enum):
        # Unknown error.
        UnknownError = -1
        # Invalid function description.
        InvalidFunctionDescription = 0
        # Function overload not supported.
        FunctionOverloadNotSupported = 1
        # Function not available.
        FunctionNotAvailable = 2
        # Function type not supported.
        FunctionTypeNotSupported = 3
        # Invalid function type.
        InvalidFunctionType = 4
        # Invalid service configuration.
        InvalidServiceConfiguration = 5
        # Service not found.
        ServiceNotFound = 6
        # Skill collection not set.
        SkillCollectionNotSet = 7
        # Represents an error that occurs when invoking a function.
        FunctionInvokeError = 8
        # Ambiguous implementation.
        AmbiguousImplementation = 9

    # The error code.
    _error_code: ErrorCodes

    def __init__(
        self,
        error_code: ErrorCodes,
        message: str,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """Initializes a new instance of the KernelError class.

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
