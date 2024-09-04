# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import ClassVar

from groq import AsyncGroq

from semantic_kernel.kernel_pydantic import KernelBaseModel


class GroqBase(KernelBaseModel, ABC):
    """Groq service base.

    Args:
        client [AsyncGroq]: An Groq client to use for the service.
    """

    MODEL_PROVIDER_NAME: ClassVar[str] = "groq"

    client: AsyncGroq
