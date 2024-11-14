# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from mistralai import Mistral

from semantic_kernel.kernel_pydantic import KernelBaseModel


class MistralAIBase(KernelBaseModel, ABC):
    """Mistral AI service base."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "mistralai"

    async_client: Mistral
