# Copyright (c) Microsoft. All rights reserved.


from enum import Enum

from pydantic import HttpUrl

from semantic_kernel.kernel_pydantic import KernelBaseModel


class OpenAIAuthenticationType(str, Enum):
    """OpenAI authentication types."""

    OAuth = "oauth"
    NoneType = "none"


class OpenAIAuthorizationType(str, Enum):
    """OpenAI authorization types."""

    Bearer = "Bearer"
    Basic = "Basic"


class OpenAIAuthenticationConfig(KernelBaseModel):
    """OpenAI authentication configuration."""

    type: OpenAIAuthenticationType | None = None
    authorization_type: OpenAIAuthorizationType | None = None
    client_url: HttpUrl | None = None
    authorization_url: HttpUrl | None = None
    authorization_content_type: str | None = None
    scope: str | None = None
    verification_tokens: dict[str, str] | None = None
