# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import urlparse

import httpx
from pydantic import Field

from semantic_kernel.connectors.openapi_plugin.operation_selection_predicate_context import (
    OperationSelectionPredicateContext,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

AuthCallbackType = Callable[..., Awaitable[Any]]


class OpenAPIFunctionExecutionParameters(KernelBaseModel):
    """OpenAPI function execution parameters.

    OpenAPI operation request URLs are validated by default to reduce SSRF risk. Requests must use HTTPS
    and must not resolve to private, loopback, link-local, or otherwise non-public IP addresses unless the
    target is explicitly trusted through `server_url_validation_allowed_base_urls` or
    `allow_private_network_access`.
    """

    http_client: httpx.AsyncClient | None = None
    auth_callback: AuthCallbackType | None = None
    server_url_override: str | None = None
    ignore_non_compliant_errors: bool = False
    user_agent: str | None = None
    enable_dynamic_payload: bool = True
    enable_payload_namespacing: bool = False
    operations_to_exclude: list[str] = Field(default_factory=list, description="The operationId(s) to exclude")
    operation_selection_predicate: Callable[[OperationSelectionPredicateContext], bool] | None = None
    timeout: float | None = Field(
        None, description="Default timeout in seconds for HTTP requests. Uses httpx default (5 seconds) if None."
    )
    enable_file_ref_resolution: bool = Field(
        False,
        description=(
            "Whether to resolve local file $ref references when parsing OpenAPI documents. "
            "Disabled by default. When False, only internal JSON pointer references are resolved. "
            "Set to True if your OpenAPI spec is split across multiple local files and you trust "
            "the document source."
        ),
    )
    enable_http_ref_resolution: bool = Field(
        False,
        description=(
            "Whether to resolve external HTTP $ref references when parsing OpenAPI documents. "
            "Disabled by default. Set to True only if you trust the OpenAPI document source "
            "and need external HTTP $ref resolution."
        ),
    )
    server_url_validation_allowed_base_urls: list[str] = Field(
        default_factory=list,
        description=(
            "Base URLs that are explicitly allowed for OpenAPI operation requests. Matching URLs bypass "
            "the default HTTPS-only and private-network validation gates. Set only for trusted endpoints."
        ),
    )
    allow_private_network_access: bool = Field(
        False,
        description=(
            "Whether OpenAPI operation requests may target private, loopback, link-local, or otherwise "
            "non-public IP addresses. Disabled by default to prevent SSRF."
        ),
    )

    def model_post_init(self, __context: Any) -> None:
        """Post initialization method for the model."""
        from semantic_kernel.connectors.openapi_plugin.server_url_validator import ServerUrlValidationOptions
        from semantic_kernel.utils.telemetry.user_agent import HTTP_USER_AGENT

        if self.server_url_override:
            parsed_url = urlparse(self.server_url_override)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid server_url_override: {self.server_url_override}")

        ServerUrlValidationOptions(allowed_base_urls=self.server_url_validation_allowed_base_urls)

        if not self.user_agent:
            self.user_agent = HTTP_USER_AGENT
