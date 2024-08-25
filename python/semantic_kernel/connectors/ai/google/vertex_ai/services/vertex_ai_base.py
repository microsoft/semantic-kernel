# Copyright (c) Microsoft. All rights reserved.

from abc import ABC

from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class VertexAIBase(KernelBaseModel, ABC):
    """Vertex AI Service."""

    service_settings: VertexAISettings
