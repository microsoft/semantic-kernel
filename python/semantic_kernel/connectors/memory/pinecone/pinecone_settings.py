# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class PineconeSettings(BaseModelSettings):
    """Pinecone model settings

    Required:
    - api_key: SecretStr - Pinecone API key
        (Env var PINECONE_API_KEY)
    """

    api_key: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "PINECONE_"
