# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.processes.kernel_process.kernel_process_map import KernelProcessMap
from semantic_kernel.processes.kernel_process.kernel_process_map_step_state_metadata import (
    KernelProcessMapStateMetadata,
)
from semantic_kernel.processes.kernel_process.kernel_process_state_metadata import KernelProcessStateMetadata
from semantic_kernel.processes.kernel_process.kernel_process_step_metadata import KernelProcessStepMetadataAttribute
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata
from semantic_kernel.processes.process_types import get_generic_state_type

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process import KernelProcess
    from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo


def extract_process_step_metadata_from_type(step_cls: type) -> KernelProcessStepMetadataAttribute:
    """Extracts the process step metadata from the type."""
    return getattr(step_cls, "_kernel_process_step_metadata", KernelProcessStepMetadataAttribute("v1"))


def kernel_process_to_process_state_metadata(kernel_process: "KernelProcess") -> KernelProcessStateMetadata:
    """Converts a kernel process to process state metadata."""
    KernelProcessStateMetadata.model_rebuild()

    metadata = KernelProcessStateMetadata(
        name=kernel_process.state.name,
        id=kernel_process.state.id,
        version_info=kernel_process.state.version,
        steps_state={},
    )

    for step in kernel_process.steps:
        metadata.steps_state[step.state.name] = to_process_state_metadata(step)

    return metadata


def to_process_state_metadata(step_info: "KernelProcessStepInfo") -> KernelProcessStepStateMetadata:
    """Converts a step info object to process state metadata."""
    from semantic_kernel.processes.kernel_process import KernelProcess

    if isinstance(step_info, KernelProcess):
        return kernel_process_to_process_state_metadata(step_info)
    if isinstance(step_info, KernelProcessMap):
        return kernel_process_map_to_process_state_metadata(step_info)

    return step_info_to_process_state_metadata(step_info)


def kernel_process_map_to_process_state_metadata(step_map: KernelProcessMap) -> KernelProcessMapStateMetadata:
    """Converts a kernel process map to process state metadata."""
    return KernelProcessMapStateMetadata(
        name=step_map.state.name,
        id=step_map.state.id,
        version_info=step_map.state.version,
        operation_state=to_process_state_metadata(step_map.operation),
    )


def step_info_to_process_state_metadata(step_info: "KernelProcessStepInfo") -> KernelProcessStepStateMetadata:
    """Converts a step info object to process state metadata."""
    metadata = KernelProcessStepStateMetadata(
        name=step_info.state.name,
        id=step_info.state.id,
        version_info=step_info.state.version,
    )

    generic_state_type = get_generic_state_type(step_info.inner_step_type)
    if generic_state_type:
        inner_state = getattr(step_info.state, "state", None)
        if inner_state is not None:
            metadata.state = inner_state

    return metadata
