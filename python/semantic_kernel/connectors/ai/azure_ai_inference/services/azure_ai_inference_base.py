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

    # All Microsoft tools/SDKs that internally use the Azure AI Inference SDK are required to set
    # a unique application ID, which will be part of the "use-agent" HTTP request header. This will
    # allow teams to track usage from that tool/SDK, using service-side telemetry dashboards.
    # Semantic Kernel's application ID is registered as "semantic-kernel". Note that the application
    # ID is set only when a custom client is not provided, unless the custom client also sets the
    # application ID.
    _APPLICATION_ID: ClassVar[str] = "semantic-kernel"

    client: ChatCompletionsClient | EmbeddingsClient

    def __del__(self) -> None:
        """Close the client when the object is deleted."""
        with contextlib.suppress(Exception):
            asyncio.get_running_loop().create_task(self.client.close())
