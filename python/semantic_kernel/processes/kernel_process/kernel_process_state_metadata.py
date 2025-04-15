# Copyright (c) Microsoft. All rights reserved.


from typing import ClassVar, Literal

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata


class KernelProcessStateMetadata(KernelProcessStepStateMetadata):
    """Process state used for State Persistence serialization."""

    type_: Literal["Process"] = Field("Process", alias="$type")
    steps_state: dict[str, "KernelProcessStateMetadata | KernelProcessStepStateMetadata"] | None = Field(
        None, alias="stepsState"
    )

    model_config: ClassVar = {
        "populate_by_name": True,
    }
