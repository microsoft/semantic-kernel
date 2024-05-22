# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings
from semantic_kernel.kernel_pydantic import HttpsUrl
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class WeaviateSettings(BaseModelSettings):
    """Weaviate model settings

    Optional:
    - url: HttpsUrl | None - Weaviate URL (Env var WEAVIATE_URL)
    - api_key: SecretStr | None - Weaviate token (Env var WEAVIATE_API_KEY)
    - use_embed: bool - Whether to use the client embedding options
        (Env var WEAVIATE_USE_EMBED)
    """

    url: HttpsUrl | None = None
    api_key: SecretStr | None = None
    use_embed: bool = False

    class Config(BaseModelSettings.Config):
        env_prefix = "WEAVIATE_"

    def validate_settings(self):
        if not self.use_embed and not self.url:
            raise ValueError("Weaviate config must have either url or use_embed set")
