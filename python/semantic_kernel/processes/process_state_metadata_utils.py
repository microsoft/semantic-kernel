# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from semantic_kernel.processes.kernel_process.kernel_process_step_metadata import KernelProcessStepMetadataAttribute
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import (
    KernelProcessStateMetadata,
    KernelProcessStepStateMetadata,
)
from semantic_kernel.processes.process_types import get_generic_state_type
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process import KernelProcess
    from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo


@experimental
def extract_process_step_metadata_from_type(step_cls: type) -> KernelProcessStepMetadataAttribute:
    """Extracts the process step metadata from the type."""
    return getattr(step_cls, "_kernel_process_step_metadata", KernelProcessStepMetadataAttribute("v1"))


@experimental
def kernel_process_to_process_state_metadata(kernel_process: "KernelProcess") -> KernelProcessStateMetadata:
    """Converts a kernel process to process state metadata."""
    KernelProcessStateMetadata.model_rebuild()

    metadata: KernelProcessStateMetadata[Any] = KernelProcessStateMetadata(
        name=kernel_process.state.name,
        id=kernel_process.state.id,
        version_info=kernel_process.state.version,
        steps_state={},
    )

    for step in kernel_process.steps:
        metadata.steps_state[step.state.name] = to_process_state_metadata(step)

    return metadata


@experimental
def to_process_state_metadata(step_info: "KernelProcessStepInfo") -> KernelProcessStepStateMetadata:
    """Converts a step info object to process state metadata."""
    from semantic_kernel.processes.kernel_process import KernelProcess

    if isinstance(step_info, KernelProcess):
        return kernel_process_to_process_state_metadata(step_info)

    return step_info_to_process_state_metadata(step_info)


@experimental
def step_info_to_process_state_metadata(step_info: "KernelProcessStepInfo") -> KernelProcessStepStateMetadata:
    """Converts a step info object to process state metadata."""
    metadata: KernelProcessStepStateMetadata[Any] = KernelProcessStepStateMetadata(
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
