# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Optional


class SKException(Exception):
    """The base class for all semantic kernel exceptions."""

    def __init__(
        self,
        error_code: Enum,
        message: Optional[str] = None,
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """Initializes a new instance of the SKException class.

        Arguments:
            error_code {Enum} -- The error code.
            message {str} -- The error message.
            inner_exception {Exception} -- The inner exception.
        """
        super().__init__(self._build_message(error_code, message), inner_exception)

    def _build_message(self, error_code: Enum, message: Optional[str]) -> str:
        if message is None:
            return error_code.name
        else:
            return f"{error_code.name}: {message}"
