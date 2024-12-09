# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field
from typing_extensions import Annotated

from semantic_kernel.processes.kernel_process.kernel_process_map_step_state_metadata import (
    KernelProcessMapStateMetadata,
)
from semantic_kernel.processes.kernel_process.kernel_process_state_metadata import KernelProcessStateMetadata
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata

process_metadata = Annotated[
    KernelProcessStateMetadata | KernelProcessMapStateMetadata | KernelProcessStepStateMetadata,
    Field(discriminator="$type"),
]
