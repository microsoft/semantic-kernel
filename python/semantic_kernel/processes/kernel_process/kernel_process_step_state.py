# Copyright (c) Microsoft. All rights reserved.

from typing import Generic, TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

TState = TypeVar("TState")


@experimental_class
class KernelProcessStepState(KernelBaseModel, Generic[TState]):
    """The state of a step in a kernel process."""

    name: str
    id: str | None = None
    state: TState | None = None
