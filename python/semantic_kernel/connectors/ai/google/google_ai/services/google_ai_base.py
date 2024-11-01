# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class GoogleAIBase(KernelBaseModel, ABC):
    """Google AI Service."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "googleai"

    service_settings: GoogleAISettings
