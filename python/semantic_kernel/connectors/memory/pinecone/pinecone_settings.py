# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings


class PineconeSettings(BaseModelSettings):
    """Pinecone model settings

    Required:
    - api_key: SecretStr - Pinecone API key
        (Env var PINECONE_API_KEY)
    """

    api_key: SecretStr | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "PINECONE_"
