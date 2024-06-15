# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class PineconeSettings(KernelBaseSettings):
    """Pinecone model settings.

    Args:
    - api_key: SecretStr - Pinecone API key
        (Env var PINECONE_API_KEY)
    """

    env_prefix: ClassVar[str] = "PINECONE_"

    api_key: SecretStr
