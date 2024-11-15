# Copyright (c) Microsoft. All rights reserved.

import logging
from contextlib import asynccontextmanager

import uvicorn
from dapr.ext.fastapi import DaprActor
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from samples.demos.process_with_dapr.process.process import get_process
from samples.demos.process_with_dapr.process.steps import CommonEvents
from semantic_kernel import Kernel
from semantic_kernel.processes.dapr_runtime import (
    register_fastapi_dapr_actors,
    start,
)

logging.basicConfig(level=logging.ERROR)


# Define the kernel that is used throughout the process
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


# Define a lifespan method that registers the actors with the Dapr runtime
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("## actor startup ##")
    await register_fastapi_dapr_actors(actor, kernel)
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
        process = get_process()

        _ = await start(
            process=process,
            kernel=kernel,
            initial_event=CommonEvents.StartProcess,
            process_id=process_id,
        )
        return JSONResponse(content={"processId": process_id}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="error")  # nosec
