# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class KernelProcessFunctionTarget(KernelBaseModel):
    """The target of a function call in a kernel process."""

    step_id: str
    function_name: str
    parameter_name: str | None = None
    target_event_id: str | None = None
