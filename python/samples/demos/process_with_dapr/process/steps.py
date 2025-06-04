# Copyright (c) Microsoft. All rights reserved.

import asyncio
from enum import Enum
from typing import ClassVar

from pydantic import Field

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
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


# Define a simple factory for the BStep that can create the dependency that the BStep requires
# As an example, this factory creates a kernel and adds an `AzureChatCompletion` service to it.
async def bstep_factory():
    """Creates a BStep instance with ephemeral references like ChatCompletionAgent."""
    agent = ChatCompletionAgent(service=AzureChatCompletion(), name="echo", instructions="repeat the input back")
    step_instance = BStep()
    step_instance.agent = agent
    step_instance.thread = ChatHistoryAgentThread()

    return step_instance


class BStep(KernelProcessStep):
    """A sample BStep that optionally holds a ChatCompletionAgent.

    By design, the agent is ephemeral (not stored in state).
    """

    # Ephemeral references won't be persisted to Dapr
    # because we do not place them in a step state model.
    # We'll set this in the factory function:
    agent: ChatCompletionAgent | None = None
    thread: ChatHistoryAgentThread | None = None

    @kernel_function(name="do_it")
    async def do_it(self, context: KernelProcessStepContext):
        print("##### BStep ran (do_it).")
        await asyncio.sleep(2)

        if self.agent:
            response = await self.agent.get_response(messages="Hello from BStep!")
            print(f"BStep got agent response: {response.content}")

        await context.emit_event(process_event="BStepDone", data="I did B")


# Define a sample `CStepState` that will keep track of the current cycle.
class CStepState(KernelBaseModel):
    current_cycle: int = 1


# Define a sample `CStep` step that will emit an `ExitRequested` event after 3 cycles.
class CStep(KernelProcessStep[CStepState]):
    state: CStepState = Field(default_factory=CStepState)

    # The activate method overrides the base class method to set the state in the step.
    async def activate(self, state: KernelProcessStepState[CStepState]):
        """Activates the step and sets the state."""
        self.state = state.state
        print(f"##### CStep activated with Cycle = '{self.state.current_cycle}'.")

    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext, astepdata: str, bstepdata: str):
        self.state.current_cycle += 1
        if self.state.current_cycle >= 3:
            print("##### CStep run cycle 3 - exiting.")
            await context.emit_event(process_event=CommonEvents.ExitRequested)
            return
        print(f"##### CStep run cycle {self.state.current_cycle}")
        await context.emit_event(process_event=CommonEvents.CStepDone)
