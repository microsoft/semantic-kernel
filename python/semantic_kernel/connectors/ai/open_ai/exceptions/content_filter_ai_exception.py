# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from openai import BadRequestError

from semantic_kernel.connectors.ai.ai_exception import AIException


class ContentFilterResultSeverity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    SAFE = "safe"


@dataclass
class ContentFilterResult:
    filtered: bool = False
    detected: bool = False
    severity: ContentFilterResultSeverity = ContentFilterResultSeverity.SAFE

    @classmethod
    def from_inner_error_result(cls, inner_error_results: Dict[str, Any]) -> "ContentFilterResult":
        """Creates a ContentFilterResult from the inner error results.

        Arguments:
            key {str} -- The key to get the inner error result from.
            inner_error_results {Dict[str, Any]} -- The inner error results.

        Returns:
            ContentFilterResult -- The ContentFilterResult.
        """
        return cls(
            filtered=inner_error_results.get("filtered", False),
            detected=inner_error_results.get("detected", False),
            severity=ContentFilterResultSeverity(
                inner_error_results.get("severity", ContentFilterResultSeverity.SAFE.value)
            ),
        )


class ContentFilterCodes(Enum):
    RESPONSIBLE_AI_POLICY_VIOLATION = "ResponsibleAIPolicyViolation"


class ContentFilterAIException(AIException):
    """AI exception for an error from Azure OpenAI's content filter"""

    # The parameter that caused the error.
    _param: str

    # The error code specific to the content filter.
    _content_filter_code: ContentFilterCodes

    # The results of the different content filter checks.
    _content_filter_result: Dict[str, ContentFilterResult]

    def __init__(
        self,
        error_code: AIException.ErrorCodes,
        message: str,
        inner_exception: BadRequestError,
    ) -> None:
        """Initializes a new instance of the ContentFilterAIException class.

        Arguments:
            error_code {ErrorCodes} -- The error code.
            message {str} -- The error message.
            inner_exception {Exception} -- The inner exception.
        """
        super().__init__(error_code, message, inner_exception)

        self._param = inner_exception.param

        inner_error = inner_exception.body.get("innererror", {})
        self._content_filter_code = ContentFilterCodes(
            inner_error.get("code", ContentFilterCodes.RESPONSIBLE_AI_POLICY_VIOLATION.value)
        )
        self._content_filter_result = dict(
            [
                key,
                ContentFilterResult.from_inner_error_result(values),
            ]
            for key, values in inner_error.get("content_filter_result", {}).items()
        )

    @property
    def param(self) -> str:
        """Gets the parameter that caused the error.

        Returns:
            str -- The parameter that caused the error.
        """
        return self._param

    @property
    def content_filter_code(self) -> ContentFilterCodes:
        """Gets the error code specific to the content filter.

        Returns:
            ContentFilterCode -- The error code specific to the content filter.
        """
        return self._content_filter_code

    @property
    def content_filter_result(self) -> Dict[str, ContentFilterResult]:
        """Gets the result of the content filter checks.

        Returns:
            Dict[str, ContentFilterResult] -- The result of the content filter checks.
        """
        return self._content_filter_result
