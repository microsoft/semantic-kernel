# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelProcessFunctionTarget(KernelBaseModel):
    """The target of a function call in a kernel process."""

    step_id: str
    function_name: str
    parameter_name: str | None = None
    target_event_id: str | None = None
