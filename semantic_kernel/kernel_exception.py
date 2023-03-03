# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Optional

from semantic_kernel.diagnostics.sk_exception import SKException


class KernelException(SKException):
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
        # Invalid backend configuration.
        InvalidBackendConfiguration = 5
        # Backend not found.
        BackendNotFound = 6
        # Skill collection not set.
        SkillCollectionNotSet = 7
        # Ambiguous implementation.
        AmbiguousImplementation = 8

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
