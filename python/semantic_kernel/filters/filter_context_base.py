# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


class FilterContextBase(KernelBaseModel):
    """Base class for Kernel Filter Contexts."""

    function: "KernelFunction"
    kernel: "Kernel"
    arguments: "KernelArguments"
    is_streaming: bool = False
