# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from enum import Enum
from typing import ClassVar

from pydantic import BaseModel, Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.process_builder import ProcessBuilder

logging.basicConfig(level=logging.WARNING)


class CommonEvents(Enum):
    """Common events for the sample process."""

    UserInputReceived = "UserInputReceived"
    CompletionResponseGenerated = "CompletionResponseGenerated"
    WelcomeDone = "WelcomeDone"
    AStepDone = "AStepDone"
    BStepDone = "BStepDone"
    CStepDone = "CStepDone"
    StartARequested = "StartARequested"
    StartBRequested = "StartBRequested"
    ExitRequested = "ExitRequested"
    StartProcess = "StartProcess"


# Define a sample step that once the `on_input_event` is received,
# it will emit two events to start the A and B steps.
class KickOffStep(KernelProcessStep):
    KICK_OFF_FUNCTION: ClassVar[str] = "kick_off"

    @kernel_function(name=KICK_OFF_FUNCTION)
    async def print_welcome_message(self, context: KernelProcessStepContext):
        await context.emit_event(process_event=CommonEvents.StartARequested, data="Get Going A")
        await context.emit_event(process_event=CommonEvents.StartBRequested, data="Get Going B")


# Define a sample `AStep` step that will emit an event after 1 second.
# The event will be sent to the `CStep` step with the data `I did A`.
class AStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        await asyncio.sleep(1)
        await context.emit_event(process_event=CommonEvents.AStepDone, data="I did A")


# Define a sample `BStep` step that will emit an event after 2 seconds.
# The event will be sent to the `CStep` step with the data `I did B`.
class BStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        await asyncio.sleep(2)
        await context.emit_event(process_event=CommonEvents.BStepDone, data="I did B")


# Define a sample `CStepState` that will keep track of the current cycle.
class CStepState(BaseModel):
    current_cycle: int = 0


# Define a sample `CStep` step that will emit an `ExitRequested` event after 3 cycles.
class CStep(KernelProcessStep[CStepState]):
    state: CStepState = Field(default_factory=CStepState)

    # The activate method overrides the base class method to set the state in the step.
    async def activate(self, state: KernelProcessStepState[CStepState]):
        """Activates the step and sets the state."""
        self.state = state.state

    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext, astepdata: str, bstepdata: str):
        self.state.current_cycle += 1
        print(f"CStep Current Cycle: {self.state.current_cycle}")
        if self.state.current_cycle == 3:
            print("CStep Exit Requested")
            await context.emit_event(process_event=CommonEvents.ExitRequested)
            return
        await context.emit_event(process_event=CommonEvents.CStepDone)


kernel = Kernel()


async def cycles_with_fan_in():
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    # Define the process builder
    process = ProcessBuilder(name="Test Process")

    # Add the step types to the builder
    kickoff_step = process.add_step(step_type=KickOffStep)
    myAStep = process.add_step(step_type=AStep)
    myBStep = process.add_step(step_type=BStep)
    myCStep = process.add_step(step_type=CStep)

    # Define the input event and where to send it to
    process.on_input_event(event_id=CommonEvents.StartProcess).send_event_to(target=kickoff_step)

    # Define the process flow
    kickoff_step.on_event(event_id=CommonEvents.StartARequested).send_event_to(target=myAStep)
    kickoff_step.on_event(event_id=CommonEvents.StartBRequested).send_event_to(target=myBStep)
    myAStep.on_event(event_id=CommonEvents.AStepDone).send_event_to(target=myCStep, parameter_name="astepdata")

    # Define the fan in behavior once both AStep and BStep are done
    myBStep.on_event(event_id=CommonEvents.BStepDone).send_event_to(target=myCStep, parameter_name="bstepdata")
    myCStep.on_event(event_id=CommonEvents.CStepDone).send_event_to(target=kickoff_step)
    myCStep.on_event(event_id=CommonEvents.ExitRequested).stop_process()

    # Build the process
    kernel_process = process.build()

    async with await start(
        process=kernel_process,
        kernel=kernel,
        initial_event=KernelProcessEvent(id=CommonEvents.StartProcess, data="foo"),
    ) as process_context:
        process_state = await process_context.get_state()
        c_step_state: KernelProcessStepState[CStepState] = next(
            (s.state for s in process_state.steps if s.state.name == "CStep"), None
        )
        assert c_step_state.state  # nosec
        assert c_step_state.state.current_cycle == 3  # nosec
        print(f"Final State Check: CStepState current cycle: {c_step_state.state.current_cycle}")


if __name__ == "__main__":
    asyncio.run(cycles_with_fan_in())
