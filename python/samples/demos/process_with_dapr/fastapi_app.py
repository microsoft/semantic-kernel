# Copyright (c) Microsoft. All rights reserved.

import logging
from contextlib import asynccontextmanager

import uvicorn
from dapr.ext.fastapi import DaprActor
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from samples.demos.process_with_dapr.process.process import get_process
from samples.demos.process_with_dapr.process.steps import CommonEvents, CStepState
from semantic_kernel import Kernel
from semantic_kernel.processes.dapr_runtime import register_fastapi_dapr_actors, start
from semantic_kernel.processes.dapr_runtime.dapr_kernel_process_context import DaprKernelProcessContext
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState

logging.basicConfig(level=logging.WARNING)


# Define the kernel that is used throughout the process
kernel = Kernel()

"""
The following Process and Dapr runtime sample uses a FastAPI app
to start a process and run steps. The process is defined in the
process/process.py file and the steps are defined in the steps.py
file. The process is started by calling the /processes/{process_id}
endpoint. The actors are registered with the Dapr runtime using
the DaprActor class. The ProcessActor and the StepActor require a
kernel dependency to be injected during creation. This is done by
defining a factory function that takes the kernel as a parameter
and returns the actor instance with the kernel injected.
"""

# Get the process which means we have the `KernelProcess` object
# along with any defined step factories
process = get_process()


# Define a lifespan method that registers the actors with the Dapr runtime
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("## actor startup ##")
    await register_fastapi_dapr_actors(actor, kernel, process.factories)
    yield


# Define the FastAPI app along with the DaprActor
app = FastAPI(title="SKProcess", lifespan=lifespan)
actor = DaprActor(app)


@app.get("/healthz")
async def healthcheck():
    return "Healthy!"


@app.get("/processes/{process_id}")
async def start_process(process_id: str):
    try:
        context: DaprKernelProcessContext = await start(
            process=process,
            kernel=kernel,
            initial_event=CommonEvents.StartProcess,
            process_id=process_id,
        )
        kernel_process = await context.get_state()

        # If desired, uncomment the following lines to see the process state
        # final_state = kernel_process.to_process_state_metadata()
        # print(final_state.model_dump(exclude_none=True, by_alias=True, mode="json"))

        c_step_state: KernelProcessStepState[CStepState] = next(
            (s.state for s in kernel_process.steps if s.state.name == "CStep"), None
        )
        c_step_state_validated = CStepState.model_validate(c_step_state.state)
        print(f"[FINAL STEP STATE]: CStepState current cycle: {c_step_state_validated.current_cycle}")
        return JSONResponse(content={"processId": process_id}, status_code=200)
    except Exception:
        return JSONResponse(content={"error": "Error starting process"}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="error")  # nosec
