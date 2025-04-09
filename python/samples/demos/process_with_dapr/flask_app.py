# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from flask import Flask, jsonify
from flask_dapr.actor import DaprActor

from samples.demos.process_with_dapr.process.process import get_process
from samples.demos.process_with_dapr.process.steps import CommonEvents
from semantic_kernel import Kernel
from semantic_kernel.processes.dapr_runtime import (
    register_flask_dapr_actors,
    start,
)

logging.basicConfig(level=logging.ERROR)

# Define the kernel that is used throughout the process
kernel = Kernel()

app = Flask("SKProcess")

# Enable DaprActor Flask extension
actor = DaprActor(app)

# Synchronously register actors
print("## actor startup ##")
register_flask_dapr_actors(actor, kernel)

# Create the global event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@app.route("/healthz", methods=["GET"])
def healthcheck():
    return "Healthy!", 200


@app.route("/processes/<process_id>", methods=["GET"])
def start_process(process_id):
    try:
        process = get_process()

        # Run the start coroutine in a synchronous manner
        asyncio.set_event_loop(loop)
        _ = asyncio.run(
            start(
                process=process,
                kernel=kernel,
                initial_event=CommonEvents.StartProcess,
                process_id=process_id,
            )
        )

        return jsonify({"processId": process_id}), 200
    except Exception:
        return jsonify({"error": "Error starting process"}), 500


# Run application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)  # nosec
