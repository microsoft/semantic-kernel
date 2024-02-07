# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Optional


class PlanningException(Exception):
    class ErrorCodes(Enum):
        # Unknown error.
        UnknownError = -1
        # Invalid goal.
        InvalidGoal = 0
        # Invalid plan.
        InvalidPlan = 1
        # Invalid configuration.
        InvalidConfiguration = 2
        # Create plan error.
        CreatePlanError = 3

    # The error code.
    _error_code: ErrorCodes

    def __init__(
        self,
        error_code: ErrorCodes,
        message: str,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """Initializes a new instance of the PlanningError class.

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
