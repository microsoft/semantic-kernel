# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from contextlib import asynccontextmanager
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

import uvicorn
from dapr.actor import ActorId
from dapr.actor.runtime.context import ActorRuntimeContext
from dapr.ext.fastapi import DaprActor, DaprApp
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import Field

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.dapr_runtime.actors.event_buffer_actor import EventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.external_event_buffer_actor import ExternalEventBufferActor
from semantic_kernel.processes.dapr_runtime.actors.message_buffer_actor import MessageBufferActor
from semantic_kernel.processes.dapr_runtime.actors.process_actor import ProcessActor
from semantic_kernel.processes.dapr_runtime.actors.step_actor import StepActor
from semantic_kernel.processes.dapr_runtime.dapr_kernel_process import start
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.process_builder import ProcessBuilder

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

logging.basicConfig(level=logging.ERROR)


kernel = Kernel()


# Define a Process Actor Factory that allows a dependency to be injected during Process Actor creation
def process_actor_factory(ctx: ActorRuntimeContext, actor_id: ActorId) -> ProcessActor:
    """Factory function to create ProcessActor instances with dependencies."""
    return ProcessActor(ctx, actor_id, kernel)


# Define a Step Actor Factory that allows a dependency to be injected during Step Actor creation
def step_actor_factory(ctx: ActorRuntimeContext, actor_id: ActorId) -> StepActor:
    """Factory function to create StepActor instances with dependencies."""
    return StepActor(ctx, actor_id, kernel=kernel)


# Define a lifespan method that registers the actors with the Dapr runtime
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("## actor startup ##")
    await actor.register_actor(ProcessActor, actor_factory=process_actor_factory)
    await actor.register_actor(StepActor, actor_factory=step_actor_factory)
    await actor.register_actor(EventBufferActor)
    await actor.register_actor(MessageBufferActor)
    await actor.register_actor(ExternalEventBufferActor)
    yield


# Define the FastAPI app along with the DaprApp and the DaprActor
app = FastAPI(title="SKProcess", lifespan=lifespan)
dapr_app = DaprApp(app)
actor = DaprActor(app)


@app.get("/healthz")
async def healthcheck():
    return "Healthy!"


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
        await context.emit_event(process_event=CommonEvents.StartARequested.value, data="Get Going A")
        await context.emit_event(process_event=CommonEvents.StartBRequested.value, data="Get Going B")


# Define a sample `AStep` step that will emit an event after 1 second.
# The event will be sent to the `CStep` step with the data `I did A`.
class AStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        print("##### AStep ran.")
        await asyncio.sleep(1)
        await context.emit_event(process_event=CommonEvents.AStepDone.value, data="I did A")


# Define a sample `BStep` step that will emit an event after 2 seconds.
# The event will be sent to the `CStep` step with the data `I did B`.
class BStep(KernelProcessStep):
    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext):
        print("##### BStep ran.")
        await asyncio.sleep(2)
        await context.emit_event(process_event=CommonEvents.BStepDone.value, data="I did B")


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
        self.state = state.state

    @kernel_function()
    async def do_it(self, context: KernelProcessStepContext, astepdata: str, bstepdata: str):
        self.state.current_cycle += 1
        if self.state.current_cycle >= 3:
            print("##### CStep run cycle 3 - exiting.")
            await context.emit_event(process_event=CommonEvents.ExitRequested.value)
            return
        print(f"##### CStep run cycle {self.state.current_cycle}")
        await context.emit_event(process_event=CommonEvents.CStepDone.value)


kernel = Kernel()


def get_process() -> "KernelProcess":
    # Define the process builder
    process = ProcessBuilder(name="ProcessWithDapr")

    # Add the step types to the builder
    kickoff_step = process.add_step(step_type=KickOffStep)
    myAStep = process.add_step(step_type=AStep)
    myBStep = process.add_step(step_type=BStep)

    # Initialize the CStep with an initial state and the state's current cycle set to 1
    myCStep = process.add_step(step_type=CStep, initial_state=CStepState(current_cycle=1))

    # Define the input event and where to send it to
    process.on_input_event(event_id=CommonEvents.StartProcess.value).send_event_to(target=kickoff_step)

    # Define the process flow
    kickoff_step.on_event(event_id=CommonEvents.StartARequested.value).send_event_to(target=myAStep)
    kickoff_step.on_event(event_id=CommonEvents.StartBRequested.value).send_event_to(target=myBStep)
    myAStep.on_event(event_id=CommonEvents.AStepDone.value).send_event_to(target=myCStep, parameter_name="astepdata")

    # Define the fan in behavior once both AStep and BStep are done
    myBStep.on_event(event_id=CommonEvents.BStepDone.value).send_event_to(target=myCStep, parameter_name="bstepdata")
    myCStep.on_event(event_id=CommonEvents.CStepDone.value).send_event_to(target=kickoff_step)
    myCStep.on_event(event_id=CommonEvents.ExitRequested.value).stop_process()

    # Build the process
    return process.build()


@app.get("/processes/{process_id}")
async def start_process(process_id: str):
    try:
        process = get_process()
        _ = await start(
            process=process, kernel=kernel, initial_event=CommonEvents.StartProcess.value, process_id=process_id
        )
        return JSONResponse(content={"processId": process_id}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="error")  # nosec
