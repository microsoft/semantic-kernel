# Copyright (c) Microsoft. All rights reserved.


from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata


class KernelProcessStateMetadata(KernelProcessStepStateMetadata):
    """Process state used for State Persistence serialization."""

    steps_state: dict[str, KernelProcessStepStateMetadata] | None = Field(None, alias="stepsState")
