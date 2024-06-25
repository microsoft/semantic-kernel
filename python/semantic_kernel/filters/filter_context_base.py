# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


@experimental_class
class FilterContextBase(KernelBaseModel):
    """Base class for Kernel Filter Contexts."""

    function: "KernelFunction"
    kernel: "Kernel"
    arguments: "KernelArguments"
