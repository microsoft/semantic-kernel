# Copyright (c) Microsoft. All rights reserved.

from typing import Generic, Literal, TypeVar

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel

TState = TypeVar("TState")


class KernelProcessStepStateMetadata(KernelBaseModel, Generic[TState]):
    """Process state used for State Persistence serialization."""

    type_: Literal["Step", "Process"] = Field("Step", alias="$type")
    id: str | None = Field(None, alias="id")
    name: str | None = Field(None, alias="name")
    version_info: str | None = Field(None, alias="versionInfo")
    state: TState | None = Field(None, alias="state")  # type: ignore[valid-type]
