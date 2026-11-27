# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass

import pytest

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import (
    KernelProcessStateMetadata,
    KernelProcessStepStateMetadata,
)
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_state_metadata_utils import kernel_process_to_process_state_metadata


class CounterState(KernelBaseModel):
    count: int = 0


@dataclass
class DataclassCounterState:
    count: int = 0


class CounterStep(KernelProcessStep[CounterState]):
    """A step that only names its state type in the base class, like the process samples do for UserInputStep."""

    async def activate(self, state: KernelProcessStepState[CounterState]):
        state.state = state.state or CounterState()
        self.state = state.state

    @kernel_function
    async def run(self, value: str) -> str:
        self.state.count += 1
        return value


class DataclassCounterStep(KernelProcessStep[DataclassCounterState]):
    async def activate(self, state: KernelProcessStepState[DataclassCounterState]):
        state.state = state.state or DataclassCounterState()
        self.state = state.state

    @kernel_function
    async def run(self, value: str) -> str:
        self.state.count += 1
        return value


def _restore_metadata(step_name: str, state: dict) -> KernelProcessStateMetadata:
    return KernelProcessStateMetadata(
        name="p",
        id=None,
        version_info="v1",
        steps_state={
            step_name: KernelProcessStepStateMetadata(name=step_name, id=None, version_info="v1", state=state)
        },
    )


@pytest.mark.parametrize(
    ("step_type", "state_type"),
    [(CounterStep, CounterState), (DataclassCounterStep, DataclassCounterState)],
    ids=["pydantic", "dataclass"],
)
def test_build_gives_a_parametrized_step_a_default_state(step_type, state_type):
    builder = ProcessBuilder(name="p")
    builder.add_step(step_type)

    process = builder.build()

    assert process.steps[0].state.state == state_type()


def test_initial_state_is_accepted_by_a_parametrized_step():
    builder = ProcessBuilder(name="p")
    builder.add_step(CounterStep, initial_state=CounterState(count=5))

    process = builder.build()

    assert process.steps[0].state.state == CounterState(count=5)


@pytest.mark.parametrize(
    ("step_type", "state_type"),
    [(CounterStep, CounterState), (DataclassCounterStep, DataclassCounterState)],
    ids=["pydantic", "dataclass"],
)
def test_state_metadata_restores_the_state_of_a_parametrized_step(step_type, state_type):
    builder = ProcessBuilder(name="p")
    builder.add_step(step_type)

    process = builder.build(state_metadata=_restore_metadata(step_type.__name__, {"count": 7}))

    restored = process.steps[0].state.state
    assert isinstance(restored, state_type)
    assert restored.count == 7


@pytest.mark.parametrize(
    ("step_type", "state_type"),
    [(CounterStep, CounterState), (DataclassCounterStep, DataclassCounterState)],
    ids=["pydantic", "dataclass"],
)
async def test_state_of_a_parametrized_step_is_saved_after_a_run(step_type, state_type):
    builder = ProcessBuilder(name="p")
    step = builder.add_step(step_type)
    builder.on_input_event("go").send_event_to(step, function_name="run", parameter_name="value")

    context = await start(process=builder.build(), kernel=Kernel(), initial_event=KernelProcessEvent(id="go", data="x"))
    metadata = kernel_process_to_process_state_metadata(await context.get_state())

    assert metadata.steps_state[step_type.__name__].state == state_type(count=1)
