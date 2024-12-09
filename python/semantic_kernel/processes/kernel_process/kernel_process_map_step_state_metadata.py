# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata


class KernelProcessMapStateMetadata(KernelProcessStepStateMetadata):
    """Map state used for State Persistence serialization."""

    # [JsonPropertyName("operationState")] -> Field(alias="operationState")

    # According to the derived type info, this should have $type = "Map"
    type: Literal["Map"] = Field("Map", alias="$type")
    operationState: KernelProcessStepStateMetadata | None = Field(None, alias="operationState")
