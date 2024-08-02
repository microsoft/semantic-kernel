# Copyright (c) Microsoft. All rights reserved.

from abc import ABC

from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class GoogleAIBase(KernelBaseModel, ABC):
    """Google AI Service."""

    service_settings: GoogleAISettings
