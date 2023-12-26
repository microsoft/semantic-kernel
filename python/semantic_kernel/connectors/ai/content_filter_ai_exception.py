# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from semantic_kernel.connectors.ai.ai_exception import AIException


class ContentFilterAIException(AIException):
    """AI exception for an error from Azure OpenAI's content filter"""

    class ContentFilterCodes(Enum):
        ResponsibleAIPolicyViolation = "ResponsibleAIPolicyViolation"

    @dataclass
    class ContentFilterResult:
        class Severity(Enum):
            High = "high"
            Medium = "medium"
            Safe = "safe"

        filtered: bool = False
        detected: bool = False
        severity: Severity = Severity.Safe

        @classmethod
        def from_inner_error_result(
            cls, inner_error_results: Dict[str, Any]
        ) -> "ContentFilterAIException.ContentFilterResult":
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
                severity=cls.Severity(
                    inner_error_results.get("severity", cls.Severity.Safe.value)
                ),
            )

    # The parameter that caused the error.
    _param: str

    # The error code specific to the content filter.
    _content_filter_code: ContentFilterCodes

    # The results of the different content filter checks.
    _content_filter_result: Dict[str, ContentFilterResult]

    def __init__(
        self,
        message: str,
        param: str,
        content_filter_code: ContentFilterCodes,
        content_filter_result: Dict[str, ContentFilterResult],
        inner_exception: Optional[Exception] = None,
    ) -> None:
        """Initializes a new instance of the ContentFilterAIException class.

        Arguments:
            message {str} -- The error message.
            param {str} -- The parameter that caused the error.
            content_filter_code {ContentFilterCode} -- The error code specific to the content filter.
            content_filter_result {Dict[str, ContentFilterResult]} -- The result of the content filter checks.
            inner_exception {Exception} -- The inner exception.
        """
        super().__init__(AIException.ErrorCodes.ServiceError, message, inner_exception)

        self._param = param
        self._content_filter_code = content_filter_code
        self._content_filter_result = content_filter_result

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
