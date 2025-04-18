# Copyright (c) Microsoft. All rights reserved.

from typing import Generic, Literal, TypeVar

from pydantic import ConfigDict, Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

TState = TypeVar("TState")


@experimental
class KernelProcessStepState(KernelBaseModel, Generic[TState]):
    """The state of a step in a kernel process."""

    type: Literal["KernelProcessStepState"] = Field(default="KernelProcessStepState")  # type: ignore

    name: str
    version: str
    id: str | None = None
    state: TState | None = None

    model_config = ConfigDict(extra="ignore")
