# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

from typing import Any

from pydantic import Field

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelHookContextBase(KernelBaseModel):
    """Base class for Kernel Hook Contexts."""

    function: KernelFunction
    arguments: KernelArguments
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_arguments: bool = Field(default=False, init_var=False)

    def update_arguments(self, new_arguments: KernelArguments):
        self.arguments = new_arguments
        self.updated_arguments = True
