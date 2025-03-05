# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelProcessEdge(KernelBaseModel):
    """Represents an edge between steps."""

    source_step_id: str
    output_target: KernelProcessFunctionTarget
