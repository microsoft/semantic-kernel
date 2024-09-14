# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
from abc import ABC
from typing import ClassVar

from azure.ai.inference.aio import ChatCompletionsClient, EmbeddingsClient

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureAIInferenceBase(KernelBaseModel, ABC):
    """Azure AI Inference Chat Completion Service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "azureai"

    client: ChatCompletionsClient | EmbeddingsClient

    def __del__(self) -> None:
        """Close the client when the object is deleted."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.client.close())
