# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from ollama import AsyncClient

from semantic_kernel.kernel_pydantic import KernelBaseModel


class OllamaBase(KernelBaseModel, ABC):
    """Ollama service base.

    Args:
        client [AsyncClient]: An Ollama client to use for the service.
    """

    MODEL_PROVIDER_NAME: ClassVar[str] = "ollama"

    client: AsyncClient
