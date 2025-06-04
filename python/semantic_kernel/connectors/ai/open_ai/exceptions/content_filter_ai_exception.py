# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from enum import Enum
from typing import Any

from openai import BadRequestError

from semantic_kernel.exceptions import ServiceContentFilterException


class ContentFilterResultSeverity(Enum):
    """The severity of the content filter result."""

    HIGH = "high"
    MEDIUM = "medium"
    SAFE = "safe"
    LOW = "low"


@dataclass
class ContentFilterResult:
    """The result of a content filter check."""

    filtered: bool = False
    detected: bool = False
    severity: ContentFilterResultSeverity = ContentFilterResultSeverity.SAFE

    @classmethod
    def from_inner_error_result(cls, inner_error_results: dict[str, Any]) -> "ContentFilterResult":
        """Creates a ContentFilterResult from the inner error results.

        Args:
            key (str): The key to get the inner error result from.
            inner_error_results (Dict[str, Any]): The inner error results.

        Returns:
            ContentFilterResult: The ContentFilterResult.
        """
        return cls(
            filtered=inner_error_results.get("filtered", False),
            detected=inner_error_results.get("detected", False),
            severity=ContentFilterResultSeverity(
                inner_error_results.get("severity", ContentFilterResultSeverity.SAFE.value)
            ),
        )


class ContentFilterCodes(Enum):
    """Content filter codes."""

    RESPONSIBLE_AI_POLICY_VIOLATION = "ResponsibleAIPolicyViolation"


@dataclass
class ContentFilterAIException(ServiceContentFilterException):
    """AI exception for an error from Azure OpenAI's content filter."""

    # The parameter that caused the error.
    param: str | None

    # The error code specific to the content filter.
    content_filter_code: ContentFilterCodes

    # The results of the different content filter checks.
    content_filter_result: dict[str, ContentFilterResult]

    def __init__(
        self,
        message: str,
        inner_exception: BadRequestError,
    ) -> None:
        """Initializes a new instance of the ContentFilterAIException class.

        Args:
            message (str): The error message.
            inner_exception (Exception): The inner exception.
        """
        super().__init__(message)

        self.param = inner_exception.param
        if inner_exception.body is not None and isinstance(inner_exception.body, dict):
            inner_error = inner_exception.body.get("innererror", {})
            self.content_filter_code = ContentFilterCodes(
                inner_error.get("code", ContentFilterCodes.RESPONSIBLE_AI_POLICY_VIOLATION.value)
            )
            self.content_filter_result = {
                key: ContentFilterResult.from_inner_error_result(values)
                for key, values in inner_error.get("content_filter_result", {}).items()
            }
