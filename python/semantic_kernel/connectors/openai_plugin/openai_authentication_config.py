# Copyright (c) Microsoft. All rights reserved.


from enum import Enum

from pydantic import HttpUrl
from typing_extensions import deprecated

from semantic_kernel.kernel_pydantic import KernelBaseModel


@deprecated("The `OpenAIAuthenticationType` class is deprecated; use the `OpenAPI` plugin instead.", category=None)
class OpenAIAuthenticationType(str, Enum):
    """OpenAI authentication types."""

    OAuth = "oauth"
    NoneType = "none"


@deprecated("The `OpenAIAuthenticationType` class is deprecated; use the `OpenAPI` plugin instead.", category=None)
class OpenAIAuthorizationType(str, Enum):
    """OpenAI authorization types."""

    Bearer = "Bearer"
    Basic = "Basic"


@deprecated("The `OpenAIAuthenticationConfig` class is deprecated; use the `OpenAPI` plugin instead.", category=None)
class OpenAIAuthenticationConfig(KernelBaseModel):
    """OpenAI authentication configuration."""

    type: OpenAIAuthenticationType | None = None
    authorization_type: OpenAIAuthorizationType | None = None
    client_url: HttpUrl | None = None
    authorization_url: HttpUrl | None = None
    authorization_content_type: str | None = None
    scope: str | None = None
    verification_tokens: dict[str, str] | None = None
