# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable, List, Optional
from urllib.parse import urlparse

from pydantic import Field

from semantic_kernel.connectors.telemetry import HTTP_USER_AGENT
from semantic_kernel.kernel_pydantic import KernelBaseModel

AuthCallbackType = Callable[[Any], None]


class OpenApiFunctionExecutionParameters(KernelBaseModel):
    http_client: Optional[Any] = None
    auth_callback: Optional[AuthCallbackType] = None
    server_url_override: Optional[str] = None  # Using str type, assuming URL will be used as string.
    ignore_non_compliant_errors: bool = False
    user_agent: Optional[str] = None
    enable_dynamic_payload: bool = True
    enable_payload_namespacing: bool = False
    operations_to_exclude: List[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        # Validate and parse the server_url_override if necessary
        if self.server_url_override:
            parsed_url = urlparse(self.server_url_override)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid server_url_override: {self.server_url_override}")

        # Set a default user agent if none is provided
        if not self.user_agent:
            self.user_agent = HTTP_USER_AGENT
