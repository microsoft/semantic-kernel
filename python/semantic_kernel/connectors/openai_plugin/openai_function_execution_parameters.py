# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, Optional

from pydantic import HttpUrl, validator

from semantic_kernel.connectors.openapi.openapi_function_execution_parameters import OpenApiFunctionExecutionParameters
from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIAuthenticationType(str, Enum):
    OAuth = "OAuth"
    NoneType = "None"


class OpenAIAuthorizationType(str, Enum):
    Bearer = "Bearer"
    Basic = "Basic"


class OpenAIAuthenticationConfig(KernelBaseModel):
    type: OpenAIAuthenticationType | None = None
    authorization_type: OpenAIAuthorizationType | None = None
    client_url: HttpUrl | None = None
    authorization_url: HttpUrl | None = None
    authorization_content_type: str | None = None
    scope: str | None = None
    verification_tokens: Dict[str, str] | None = None

    @validator("type", pre=True)
    def normalize_type(cls, value):
        if value.lower() == "none":
            return "None"  # Convert 'none' to 'None'
        return value


OpenAIAuthCallbackType = Callable[[Any], None]


class OpenAIFunctionExecutionParameters(OpenApiFunctionExecutionParameters):
    auth_callback: Optional[OpenAIAuthCallbackType] = None

    # def model_post_init(self, __context: Any) -> None:
    #     super().__post_init__()
    #     # Any additional initialization or validation specific to OpenAI can go here.

    #     # Note: If there's a significant difference in how the OpenAI auth callback is used
    #     # compared to the base class's auth callback, ensure your logic in using this class
    #     # accounts for that difference. Since Python doesn't support method overloading in
    #     # the same way as C#, you'll need to ensure that usage of `auth_callback` is clear
    #     # in context.
