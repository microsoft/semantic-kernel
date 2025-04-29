# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class PineconeSettings(KernelBaseSettings):
    """Pinecone model settings.

    Args:
    - api_key: SecretStr - Pinecone API key
        (Env var PINECONE_API_KEY)
    - namespace: str - Pinecone namespace (optional, default is "")
    - embed_model: str - Embedding model (optional, default is None)
        (Env var PINECONE_EMBED_MODEL)
    """

    env_prefix: ClassVar[str] = "PINECONE_"

    api_key: SecretStr
    namespace: str = ""
    embed_model: str | None = None
