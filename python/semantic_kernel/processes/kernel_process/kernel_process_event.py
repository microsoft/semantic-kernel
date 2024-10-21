# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelProcessEventVisibility(Enum):
    """Visibility of a kernel process event."""

    Public = "Public"
    Internal = "Internal"


class KernelProcessEvent(KernelBaseModel):
    """A kernel process event."""

    id: str
    data: Any | None = None
    visibility: KernelProcessEventVisibility = KernelProcessEventVisibility.Internal
