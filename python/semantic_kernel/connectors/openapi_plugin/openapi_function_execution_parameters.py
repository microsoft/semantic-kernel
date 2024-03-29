# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from typing import Any, Awaitable, Callable, List
from urllib.parse import urlparse

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


AuthCallbackType = Callable[..., Awaitable[Any]]


class OpenAPIFunctionExecutionParameters(KernelBaseModel):
    """OpenAPI function execution parameters."""

    http_client: Any | None = None
    auth_callback: AuthCallbackType | None = None
    server_url_override: str | None = None
    ignore_non_compliant_errors: bool = False
    user_agent: str | None = None
    enable_dynamic_payload: bool = True
    enable_payload_namespacing: bool = False
    operations_to_exclude: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT

        if self.server_url_override:
            parsed_url = urlparse(self.server_url_override)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid server_url_override: {self.server_url_override}")

        if not self.user_agent:
            self.user_agent = HTTP_USER_AGENT
