# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
def find_input_channels(
    channel: KernelProcessMessageChannel, functions: dict[str, KernelFunction]
) -> dict[str, dict[str, Any | None]]:
    """Finds and creates input channels."""
    if not functions:
        raise ValueError("The step has not been initialized.")

    inputs: dict[str, Any] = {}
    for name, function in functions.items():
        inputs[name] = {}
        for param in function.metadata.parameters:
            # Check for Kernel, and skip if necessary, since it is populated later on
            if param.type_ == "Kernel":
                continue
            if not param.is_required:
                continue
            if param.type_ == "KernelProcessStepContext":
                inputs[name][param.name] = KernelProcessStepContext(channel)
            else:
                inputs[name][param.name] = None

    return inputs


@experimental
def get_fully_qualified_name(cls) -> str:
    """Gets the fully qualified name of a class."""
    return f"{cls.__module__}.{cls.__name__}"
