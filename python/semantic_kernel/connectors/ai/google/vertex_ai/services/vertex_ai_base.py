# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import (
    VertexAISettings,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel


class VertexAIBase(KernelBaseModel, ABC):
    """Vertex AI Service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "vertexai"

    service_settings: VertexAISettings
