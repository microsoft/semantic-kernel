# Semantic Kernel Processes in Dapr

This demo contains an ASP.NET core API that uses Local Runtime to run a Semantic Kernel Process. Local Runtime is a portable, event-driven runtime that can simplify the process of building resilient, stateful application that run in the cloud and/or edge. Local Runtime is a natural fit for hosting Semantic Kernel Processes and allows you to scale your processes in size and quantity without sacrificing performance, or reliability.

For more information about Semantic Kernel Processes, see the following documentation:

#### Semantic Kernel Processes

- [Overview of the Process Framework (docs)](https://learn.microsoft.com/semantic-kernel/frameworks/process/process-framework)
- [Getting Started with Processes (samples)](../../GettingStartedWithProcesses/)


## Running the Demo

```mermaid
flowchart LR
    Kickoff --> A
    Kickoff --> B
    A --> C
    B --> C

    C -->|Count < 3| Kickoff
    C -->|Count == 3| End

    classDef kickoffClass fill:#f9f,stroke:#333,stroke-width:2px;
    class Kickoff kickoffClass;

    End((End))
```

1. Build and run the sample.
2. When the service is up and running, it will expose a single API in localhost port 5000.

#### Invoking the process:

1. Open a web browser and point it to [http://localhost:5000/processes/1234](http://localhost:5000/processes/1234) to invoke a new process with `Id = "1234"`
1. You should see console output from the running service with logs that match the following:

```csharp
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

```csharp
##### Kickoff ran.
##### AStep ran.
##### BStep ran.
##### CStep run cycle 3 - exiting.
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

If you create a new instance of the process with `Id = "ABCD"` by pointing your browser to [http://localhost:5000/processes/ABCD](http://localhost:5000/processes/ABCD), you will see the it will start with the initial state as expected.

## Understanding the Code

Below are the key aspects of the code that show how Dapr and Semantic Kernel Processes can be integrated into an ASP.Net Core Web Api:

- Create a new ASP.Net web API project.
- Add the required Semantic Kernel and Dapr packages to your project:

  **_Semantic Kernel Packages_**

  - `dotnet add package Microsoft.SemanticKernel --version 1.24.0`
  - `dotnet add package Microsoft.SemanticKernel.Process.Core --version 1.24.0-alpha`
  - `dotnet add package Microsoft.SemanticKernel.Process.Runtime.Dapr --version 1.24.0-alpha`

- Build and run a Process as you normally would. For this Demo we run a simple example process from with a Controller's action method in response to a GET request. [See Controller here](./Controllers/ProcessController.cs).
