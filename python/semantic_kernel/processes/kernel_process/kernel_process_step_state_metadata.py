# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step_state import TState


class KernelProcessStepStateMetadata(KernelBaseModel):
    """Process state used for State Persistence serialization."""

    type_: Literal["Step", "Process"] = Field("Step", alias="$type")
    id: str | None = Field(None, alias="id")
    name: str | None = Field(None, alias="name")
    version_info: str | None = Field(None, alias="versionInfo")
    state: TState | None = Field(None, alias="state")
