# Copyright (c) Microsoft. All rights reserved.

import asyncio
from enum import Enum
from typing import ClassVar

from pydantic import Field

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process import (
    KernelProcessStep,
    KernelProcessStepContext,
    KernelProcessStepState,
)


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
        print("##### Kickoff ran.")
        await context.emit_event(process_event=CommonEvents.StartARequested, data="Get Going A")
        await context.emit_event(process_event=CommonEvents.StartBRequested, data="Get Going B")


# Define a sample `AStep` step that will emit an event after 1 second.
# The event will be sent to the `CStep` step with the data `I did A`.
class AStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        print("##### AStep ran.")
        await asyncio.sleep(1)
        await context.emit_event(process_event=CommonEvents.AStepDone, data="I did A")


# Define a sample `BStep` step that will emit an event after 2 seconds.
# The event will be sent to the `CStep` step with the data `I did B`.
class BStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        print("##### BStep ran.")
        await asyncio.sleep(2)
        await context.emit_event(process_event=CommonEvents.BStepDone, data="I did B")


# Define a sample `CStepState` that will keep track of the current cycle.
class CStepState(KernelBaseModel):
    current_cycle: int = 1


# Define a sample `CStep` step that will emit an `ExitRequested` event after 3 cycles.
class CStep(KernelProcessStep[CStepState]):
    state: CStepState = Field(default_factory=CStepState)

    # The activate method overrides the base class method to set the state in the step.
    async def activate(self, state: KernelProcessStepState[CStepState]):
        """Activates the step and sets the state."""
        step_state = CStepState.model_validate(state.state)
        print(f"##### CStep activated with Cycle = '{step_state.current_cycle}'.")
        self.state = step_state

    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext, astepdata: str, bstepdata: str):
        self.state.current_cycle += 1
        if self.state.current_cycle >= 3:
            print("##### CStep run cycle 3 - exiting.")
            await context.emit_event(process_event=CommonEvents.ExitRequested)
            return
        print(f"##### CStep run cycle {self.state.current_cycle}")
        await context.emit_event(process_event=CommonEvents.CStepDone)
