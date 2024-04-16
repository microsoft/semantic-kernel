# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


class KernelHookContextBase(KernelBaseModel):
    """Base class for Kernel Hook Contexts."""

    function: "KernelFunction"
    kernel: "Kernel"
    arguments: KernelArguments
    metadata: dict[str, Any] = Field(default_factory=dict)
