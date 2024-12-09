# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.processes.kernel_process.kernel_process_map import KernelProcessMap
from semantic_kernel.processes.kernel_process.kernel_process_map_step_state_metadata import (
    KernelProcessMapStateMetadata,
)
from semantic_kernel.processes.kernel_process.kernel_process_state_metadata import KernelProcessStateMetadata
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata
from semantic_kernel.processes.process_types import get_generic_state_type

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process import KernelProcess
    from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo


def kernel_process_to_process_state_metadata(kernel_process: "KernelProcess") -> KernelProcessStateMetadata:
    """Converts a kernel process to process state metadata."""
    # We assume `kernel_process.State` has attributes: Name, Id, Version
    # and `kernel_process.Steps` is iterable of step info objects.
    metadata = KernelProcessStateMetadata(
        name=kernel_process.state.name,
        id=kernel_process.state.id,
        versionInfo=kernel_process.state.version,
        steps_state={},
    )

    for step in kernel_process.steps:
        metadata.steps_state[step.state.name] = to_process_state_metadata(step)

    return metadata


def to_process_state_metadata(step_info: KernelProcessStepInfo) -> KernelProcessStepStateMetadata:
    """Converts a step info object to process state metadata."""
    # We assume type-checking against your Python classes similar to C# type checks:
    # KernelProcess, KernelProcessMap, etc.

    if is_kernel_process(step_info):
        return kernel_process_to_process_state_metadata(step_info)
    if is_kernel_process_map(step_info):
        return kernel_process_map_to_process_state_metadata(step_info)
    return step_info_to_process_state_metadata(step_info)


def kernel_process_map_to_process_state_metadata(step_map: KernelProcessMap) -> KernelProcessMapStateMetadata:
    """Converts a kernel process map to process state metadata."""
    return KernelProcessMapStateMetadata(
        name=step_map.state.name,
        id=step_map.state.id,
        versionInfo=step_map.state.version,
        operationState=to_process_state_metadata(step_map.operation),
    )


def step_info_to_process_state_metadata(step_info: "KernelProcessStepInfo") -> KernelProcessStepStateMetadata:
    """Converts a step info object to process state metadata."""
    metadata = KernelProcessStepStateMetadata(
        name=step_info.state.name, id=step_info.state.id, versionInfo=step_info.state.version
    )

    # Reflective logic in C#:
    # In Python, assume a method on `step_info.InnerStepType` that checks
    # if it is a subtype of a "stateful" step and retrieve a user state if it exists.
    # Adjust this logic as needed based on your Python equivalents.

    if get_generic_state_type(step_info.inner_step_type) is not None:
        # Hypothetical logic:
        # The C# code retrieves `innerState` via reflection:
        # In Python, suppose `step_info.State` has a `State` attribute for user-defined state.
        inner_state = getattr(step_info.state, "state", None)
        if inner_state is not None:
            metadata.state = inner_state

    return metadata


# Helper functions to determine type (replace with your actual logic):
def is_kernel_process(obj) -> bool:
    """Checks if the object is an instance of KernelProcess."""
    # Implement a check to see if obj is instance of KernelProcess
    return hasattr(obj, "Steps") and hasattr(obj, "State")  # Example placeholder


def is_kernel_process_map(obj) -> bool:
    """Checks if the object is an instance of KernelProcessMap."""
    # Implement a check to see if obj is instance of KernelProcessMap
    return hasattr(obj, "Operation") and hasattr(obj, "State")  # Example placeholder
