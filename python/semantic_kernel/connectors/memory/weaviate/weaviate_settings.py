# Copyright (c) Microsoft. All rights reserved.

from typing import Any, ClassVar

from pydantic import SecretStr, ValidationError, model_validator

from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class WeaviateSettings(KernelBaseSettings):
    """Weaviate model settings.

    Args:
        url: HttpsUrl | None - Weaviate URL (Env var WEAVIATE_URL)
        api_key: SecretStr | None - Weaviate token (Env var WEAVIATE_API_KEY)
        use_embed: bool - Whether to use the client embedding options
          (Env var WEAVIATE_USE_EMBED)
    """

    env_prefix: ClassVar[str] = "WEAVIATE_"

    url: HttpsUrl | None = None
    api_key: SecretStr | None = None
    use_embed: bool = False

    @model_validator(mode="before")
    @classmethod
    def validate_settings(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Validate Weaviate settings."""
        if not data.get("use_embed") and not data.get("url"):
            raise ValidationError("Weaviate config must have either url or use_embed set")
        return data
