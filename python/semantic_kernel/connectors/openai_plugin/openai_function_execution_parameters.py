# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx
from pydantic import Field
from typing_extensions import deprecated

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.openapi_plugin import (
        OperationSelectionPredicateContext,
    )

OpenAIAuthCallbackType = Callable[..., Awaitable[Any]]


@deprecated(
    "The `OpenAIFunctionExecutionParameters` class is deprecated; use the `OpenAPI` plugin instead.", category=None
)
class OpenAIFunctionExecutionParameters(KernelBaseModel):
    """OpenAI function execution parameters."""

    auth_callback: OpenAIAuthCallbackType | None = None
    http_client: httpx.AsyncClient | None = None
    server_url_override: str | None = None
    ignore_non_compliant_errors: bool = False
    user_agent: str | None = None
    enable_dynamic_payload: bool = True
    enable_payload_namespacing: bool = False
    operations_to_exclude: list[str] = Field(default_factory=list, description="The operationId(s) to exclude")
    operation_selection_predicate: Callable[["OperationSelectionPredicateContext"], bool] | None = None

    def model_post_init(self, __context: Any) -> None:
        """Post initialization method for the model."""
        from semantic_kernel.utils.telemetry.user_agent import HTTP_USER_AGENT

        if self.server_url_override:
            parsed_url = urlparse(self.server_url_override)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid server_url_override: {self.server_url_override}")

        if not self.user_agent:
            self.user_agent = HTTP_USER_AGENT
