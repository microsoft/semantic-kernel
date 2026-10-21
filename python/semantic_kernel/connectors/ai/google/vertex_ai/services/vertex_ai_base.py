# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from typing_extensions import deprecated

from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


@deprecated("VertexAIBase is deprecated and will be removed after 01/01/2026. Use google_ai connectors instead.")
class VertexAIBase(KernelBaseModel, ABC):
    """Vertex AI Service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "vertexai"

    service_settings: VertexAISettings
