# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata


class KernelProcessStateMetadata(KernelProcessStepStateMetadata):
    """Process state used for State Persistence serialization."""

    # [JsonPropertyName("stepsState")] -> Field(alias="stepsState")

    # According to the derived type info, this should have $type = "Process"
    type: Literal["Process"] = Field("Process", alias="$type")
    steps_state: dict[str, KernelProcessStepStateMetadata] | None = Field(None, alias="stepsState")
