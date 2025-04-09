# Semantic Kernel Processes in Dapr

This demo contains a FastAPI app that uses Dapr to run a Semantic Kernel Process. Dapr is a portable, event-driven runtime that can simplify the process of building resilient, stateful application that run in the cloud and/or edge. Dapr is a natural fit for hosting Semantic Kernel Processes and allows you to scale your processes in size and quantity without sacrificing performance, or reliability.

For more information about Semantic Kernel Processes and Dapr, see the following documentation:

#### Semantic Kernel Processes

- [Overview of the Process Framework (docs)](https://learn.microsoft.com/semantic-kernel/frameworks/process/process-framework)
- [Getting Started with Processes (samples)](../../getting_started_with_processes/)
- [Semantic Kernel Dapr Runtime](../../../semantic_kernel/processes/dapr_runtime/)

#### Dapr

- [Dapr documentation](https://docs.dapr.io/)
- [Dapr Actor documentation](https://v1-10.docs.dapr.io/developing-applications/building-blocks/actors/)
- [Dapr local development](https://docs.dapr.io/getting-started/install-dapr-selfhost/)

### Supported Dapr Extensions:

| Extension    |  Supported |
|--------------------|:----:|
| FastAPI              | ✅ | 
| Flask                | ✅ | 
| gRPC                 | ❌ | 
| Dapr Workflow        | ❌ | 

## Running the Demo

Before running this Demo, make sure to configure Dapr for local development following the links above. The Dapr containers must be running for this demo application to run.

```mermaid
flowchart LR
    Kickoff --> A
    Kickoff --> B
    A --> C
    B --> C

    C -->|Count < 3| Kickoff
    C -->|Count >= 3| End

    classDef kickoffClass fill:#f9f,stroke:#333,stroke-width:2px;
    class Kickoff kickoffClass;

    End((End))
```

1. Build and run the sample. Running the Dapr service locally can be done using the Dapr Cli or with the Dapr VS Code extension. The VS Code extension is the recommended approach if you want to debug the code as it runs.
   - If using VSCode to debug, select either the `Python FastAPI App with Dapr` or the `Python Flask API App with Dapr` option from the Run and Debug dropdown list.
1. When the service is up and running, it will expose a single API in localhost port 5001.

#### Invoking the process:

1. Open a web browser and point it to [http://localhost:5001/processes/1234](http://localhost:5001/processes/1234) to invoke a new process with `Id = "1234"`
1. When the process is complete, you should see `{"processId":"1234"}` in the web browser.
1. You should also see console output from the running service with logs that match the following:

```text
##### Kickoff ran.
##### AStep ran.
##### BStep ran.
##### CStep activated with Cycle = '1'.
##### CStep run cycle 2.
##### Kickoff ran.
##### AStep ran.
##### BStep ran.
##### CStep run cycle 3 - exiting.
```

Now refresh the page in your browser to run the same processes instance again. Now the logs should look like this:

```text
##### Kickoff ran.
##### AStep ran.
##### BStep ran.
##### CStep run cycle 4 - exiting.
```

Notice that the logs from the two runs are not the same. In the first run, the processes has not been run before and so it's initial
state came from what we defined in the process:

**_First Run_**

- `CState` is initialized with `Cycle = 1` which is the initial state that we specified while building the process.
- `CState` is invoked a total of two times before the terminal condition of `Cycle >= 3` is reached.

In the second run however, the process has persisted state from the first run:

**_Second Run_**

- `CState` is initialized with `Cycle = 3` which is the final state from the first run of the process.
- `CState` is invoked only once and is already in the terminal condition of `Cycle >= 3`.

If you create a new instance of the process with `Id = "ABCD"` by pointing your browser to [http://localhost:5001/processes/ABCD](http://localhost:5001/processes/ABCD), you will see the it will start with the initial state as expected.

## Understanding the Code

Below are the key aspects of the code that show how Dapr and Semantic Kernel Processes can be integrated into a FastAPI app:

- Create a new Dapr FastAPI app.
- Add the required Semantic Kernel and Dapr packages to your project:

**_General Imports and Dapr Packages_**

**_FastAPI App_**

```python
import logging
from contextlib import asynccontextmanager

import uvicorn
from dapr.ext.fastapi import DaprActor
from fastapi import FastAPI
from fastapi.responses import JSONResponse
```

**_Flask API App_**

```python
import asyncio
import logging

from flask import Flask, jsonify
from flask_dapr.actor import DaprActor
```

**_Semantic Kernel Process Imports_**

```python
from samples.demos.process_with_dapr.process.process import get_process
from samples.demos.process_with_dapr.process.steps import CommonEvents
from semantic_kernel import Kernel
from semantic_kernel.processes.dapr_runtime import (
    register_fastapi_dapr_actors,
    start,
)
```

**_Define the FastAPI app, Dapr App, and the DaprActor_**

```python
# Define the kernel that is used throughout the process
kernel = Kernel()


# Define a lifespan method that registers the actors with the Dapr runtime
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("## actor startup ##")
    await register_fastapi_dapr_actors(actor, kernel)
    yield


# Define the FastAPI app along with the DaprActor
app = FastAPI(title="SKProcess", lifespan=lifespan)
actor = DaprActor(app)
```

If using Flask, you will define:

```python
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
```

- Build and run a Process as you normally would. For this Demo we run a simple example process from with either a FastAPI or a Flask API method in response to a GET request. 
- [See the FastAPI app here](./fastapi_app.py).
- [See the Flask API app here](./flask_app.py)
