# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEventVisibility
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_types import TState

logging.basicConfig(level=logging.WARNING)


class ProcessEvents(Enum):
    StartProcess = "StartProcess"
    StartInnerProcess = "StartInnerProcess"
    OutputReadyPublic = "OutputReadyPublic"
    OutputReadyInternal = "OutputReadyInternal"


class StepState(BaseModel):
    last_message: str = None


class EchoStep(KernelProcessStep):
    ECHO: ClassVar[str] = "echo"

    @kernel_function(name=ECHO)
    async def echo(self, message: str):
        print(f"[ECHO] {message}")
        return message


class RepeatStep(KernelProcessStep[StepState]):
    REPEAT: ClassVar[str] = "repeat"

    state: StepState = Field(default_factory=StepState)

    async def activate(self, state: KernelProcessStepState[TState]):
        """Activates the step and sets the state."""
        self.state = state.state

    @kernel_function(name=REPEAT)
    async def repeat(self, message: str, context: KernelProcessStepContext, count: int = 2):
        output = " ".join([message] * count)
        self.state.last_message = output
        print(f"[REPEAT] {output}")

        await context.emit_event(
            process_event=ProcessEvents.OutputReadyPublic,
            data=output,
            visibility=KernelProcessEventVisibility.Public,
        )
        await context.emit_event(
            process_event=ProcessEvents.OutputReadyInternal,
            data=output,
            visibility=KernelProcessEventVisibility.Internal,
        )


def create_linear_process(name: str):
    process_builder = ProcessBuilder(name=name)
    echo_step = process_builder.add_step(step_type=EchoStep)
    repeat_step = process_builder.add_step(step_type=RepeatStep)

    process_builder.on_input_event(event_id=ProcessEvents.StartProcess).send_event_to(target=echo_step)

    echo_step.on_function_result(function_name=EchoStep.ECHO).send_event_to(
        target=repeat_step, parameter_name="message"
    )

    return process_builder


kernel = Kernel()


async def nested_process():
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    process_builder = create_linear_process("Outer")

    nested_process_step = process_builder.add_step_from_process(create_linear_process("Inner"))

    process_builder.steps[1].on_event(ProcessEvents.OutputReadyInternal).send_event_to(
        nested_process_step.where_input_event_is(ProcessEvents.StartProcess)
    )

    process = process_builder.build()

    test_input = "Test"

    process_handle = await start(
        process=process, kernel=kernel, initial_event=ProcessEvents.StartProcess, data=test_input
    )
    process_info = await process_handle.get_state()

    inner_process: KernelProcess = next((s for s in process_info.steps if s.state.name == "Inner"), None)

    repeat_step_state: KernelProcessStepState[StepState] = next(
        (s.state for s in inner_process.steps if s.state.name == "RepeatStep"), None
    )
    assert repeat_step_state.state  # nosec
    assert repeat_step_state.state.last_message == "Test Test Test Test"  # nosec


if __name__ == "__main__":
    asyncio.run(nested_process())
