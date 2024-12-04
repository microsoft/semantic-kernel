# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState

TState = TypeVar("TState")


@experimental_class
class KernelProcessStep(ABC, KernelBaseModel, Generic[TState]):
    """A KernelProcessStep Base class for process steps."""

    state: TState | None = None

    async def activate(self, state: "KernelProcessStepState[TState]"):
        """Activates the step and sets the state."""
        pass  # pragma: no cover
