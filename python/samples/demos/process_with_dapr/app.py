# Copyright (c) Microsoft. All rights reserved.

import logging
from contextlib import asynccontextmanager

import uvicorn
from dapr.actor import ActorId
from dapr.actor.runtime.context import ActorRuntimeContext
from dapr.ext.fastapi import DaprActor, DaprApp
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from samples.demos.process_with_dapr.process.process import get_process
from samples.demos.process_with_dapr.process.steps import CommonEvents
from semantic_kernel import Kernel
from semantic_kernel.processes.dapr_runtime import (
    EventBufferActor,
    ExternalEventBufferActor,
    MessageBufferActor,
    ProcessActor,
    StepActor,
    start,
)

logging.basicConfig(level=logging.ERROR)


kernel = Kernel()

#########################################################################
# The following Process and Dapr runtime sample uses a FastAPI app      #
# to start a process and run steps. The process is defined in the       #
# process/process.py file and the steps are defined in the steps.py     #
# file. The process is started by calling the /processes/{process_id}   #
# endpoint. The actors are registered with the Dapr runtime using       #
# the DaprActor class. The ProcessActor and the StepActor require a     #
# kernel dependency to be injected during creation. This is done by     #
# defining a factory function that takes the kernel as a parameter      #
# and returns the actor instance with the kernel injected.              #
#########################################################################


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
    # The process actor is used to manage the process: it starts, stops, and sends events to the process
    await actor.register_actor(ProcessActor, actor_factory=process_actor_factory)
    # The step actor is used to run the process steps
    await actor.register_actor(StepActor, actor_factory=step_actor_factory)
    # The event buffer actor is used to handle incoming events and is used by a step to bubble up events
    await actor.register_actor(EventBufferActor)
    # The message buffer actor is used to handle incoming messages from edges
    await actor.register_actor(MessageBufferActor)
    # The external event buffer actor handles incoming events to kick off a process
    await actor.register_actor(ExternalEventBufferActor)
    yield


# Define the FastAPI app along with the DaprApp and the DaprActor
app = FastAPI(title="SKProcess", lifespan=lifespan)
dapr_app = DaprApp(app)
actor = DaprActor(app)


@app.get("/healthz")
async def healthcheck():
    return "Healthy!"


@app.get("/processes/{process_id}")
async def start_process(process_id: str):
    try:
        process = get_process()

        _ = await start(
            process=process,
            kernel=kernel,
            initial_event=CommonEvents.StartProcess.value,
            process_id=process_id,
        )
        return JSONResponse(content={"processId": process_id}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="error")  # nosec
