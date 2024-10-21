# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.processes.process_types import TState

logging.basicConfig(level=logging.WARNING)


class CommonEvents:
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


class KickOffStep(KernelProcessStep):
    class Functions:
        KickOff = "kick_off"

    @kernel_function(name=Functions.KickOff)
    async def print_welcome_message(self, context: KernelProcessStepContext):
        await context.emit_event(KernelProcessEvent(id=CommonEvents.StartARequested, data="Get Going A"))
        await context.emit_event(KernelProcessEvent(id=CommonEvents.StartBRequested, data="Get Going B"))


class AStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        await asyncio.sleep(1)
        await context.emit_event(KernelProcessEvent(id=CommonEvents.AStepDone, data="I did A"))


class BStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        await asyncio.sleep(2)
        await context.emit_event(KernelProcessEvent(id=CommonEvents.BStepDone, data="I did B"))


class CStepState:
    current_cycle: int = 0


class CStep(KernelProcessStep[CStepState]):
    state: CStepState = Field(default_factory=CStepState)

    async def activate(self, state: KernelProcessStepState[TState]):
        """Activates the step and sets the state."""
        self.state = state.state

    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext, astepdata: str, bstepdata: str):
        self.state.current_cycle += 1
        print(f"CStep Current Cycle: {self.state.current_cycle}")
        if self.state.current_cycle == 3:
            await context.emit_event(process_event=KernelProcessEvent(id=CommonEvents.ExitRequested))
            return
        await context.emit_event(process_event=KernelProcessEvent(id=CommonEvents.CStepDone))


kernel = Kernel()


async def cycles_with_fan_in():
    kernel.add_service(OpenAIChatCompletion(service_id="default"))

    process = ProcessBuilder(name="Test Process")

    kickoff_step = process.add_step_from_type(step_type=KickOffStep)
    myAStep = process.add_step_from_type(step_type=AStep)
    myBStep = process.add_step_from_type(step_type=BStep)
    myCStep = process.add_step_from_type(step_type=CStep, initial_state=CStepState())

    process.on_input_event(event_id=CommonEvents.StartProcess).send_event_to(
        target=ProcessFunctionTargetBuilder(step=kickoff_step)
    )
    kickoff_step.on_event(event_id=CommonEvents.StartARequested).send_event_to(
        target=ProcessFunctionTargetBuilder(step=myAStep)
    )
    kickoff_step.on_event(event_id=CommonEvents.StartBRequested).send_event_to(
        target=ProcessFunctionTargetBuilder(step=myBStep)
    )
    myAStep.on_event(event_id=CommonEvents.AStepDone).send_event_to(
        target=ProcessFunctionTargetBuilder(step=myCStep, parameter_name="astepdata")
    )
    myBStep.on_event(event_id=CommonEvents.BStepDone).send_event_to(
        target=ProcessFunctionTargetBuilder(step=myCStep, parameter_name="bstepdata")
    )
    myCStep.on_event(event_id=CommonEvents.CStepDone).send_event_to(
        target=ProcessFunctionTargetBuilder(step=kickoff_step)
    )
    myCStep.on_event(event_id=CommonEvents.ExitRequested).stop_process()

    kernel_process = process.build()

    process_context = await kernel_process.start(
        kernel=kernel, initial_event=KernelProcessEvent(id=CommonEvents.StartProcess, data="foo")
    )

    process_state = await process_context.get_state()
    c_step_state: KernelProcessStepState[CStepState] = next(
        (s.state for s in process_state.steps if s.state.name == "CStep"), None
    )
    assert c_step_state.state  # nosec
    assert c_step_state.state.current_cycle == 3  # nosec
    print(f"CStepState current cycle: {c_step_state.state.current_cycle}")


if __name__ == "__main__":
    asyncio.run(cycles_with_fan_in())
