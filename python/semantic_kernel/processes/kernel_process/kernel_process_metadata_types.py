# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_state_metadata import KernelProcessStateMetadata
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata

process_metadata = Annotated[
    KernelProcessStateMetadata | KernelProcessStepStateMetadata,
    Field(discriminator="$type"),
]
