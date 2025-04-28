
[Instructions](https://microsoft.sharepoint.com/:fl:/s/d7d62e80-5c91-4983-b6e6-99fd6f434c15/EVoJdTVyY4dAtQneMf4X0YUBrkIOXFSj-ITNNdHor4xQsA?e=yGRoWs&nav=cz0lMkZzaXRlcyUyRmQ3ZDYyZTgwLTVjOTEtNDk4My1iNmU2LTk5ZmQ2ZjQzNGMxNSZkPWIhQ3pnR2N1RXBtazJlcjFTSEw0bkxyamZSMnpjR0tuQlBpSlBNUWRhY3lyQW1ENTF6dTVxUlRwWnR6Z2VYU0R4SyZmPTAxWFhFRDQ2SzJCRjJUSzRURFE1QUxLQ082R0g3QlBVTUYmYz0lMkYmZmx1aWQ9MSZhPUxvb3BBcHAmcD0lNDBmbHVpZHglMkZsb29wLXBhZ2UtY29udGFpbmVyJng9JTdCJTIydyUyMiUzQSUyMlQwUlRVSHh0YVdOeWIzTnZablF1YzJoaGNtVndiMmx1ZEM1amIyMThZaUZEZW1kSFkzVkZjRzFyTW1WeU1WTklURFJ1VEhKcVpsSXllbU5IUzI1Q1VHbEtVRTFSWkdGamVYSkJiVVExTVhwMU5YRlNWSEJhZEhwblpWaFRSSGhMZkRBeFdGaEZSRFEyVGxkSlNEZEhSa05IVWsxU1JVdzNWamRVU2pRMVMxZFhWRkUlM0QlMjIlMkMlMjJpJTIyJTNBJTIyZDZiMzA0ODEtZDUyYy00NzgwLWEwNTktY2M1ZmRlMWVmZTk3JTIyJTdE)

## Copy template

Starting point:
- C# console project
- Packages referenced

    ```sh
    dotnet add package Microsoft.SemanticKernel.Agents.Core
    dotnet add package Microsoft.SemanticKernel.Agents.AzureAI

    dotnet add package Microsoft.SemanticKernel.Connectors.AzureOpenAI
    dotnet add package Microsoft.SemanticKernel.Connectors.AzureAIInference --prerelease
    ```

    ```sh
    dotnet add package Microsoft.Extensions.Configuration
    dotnet add package Microsoft.Extensions.Configuration.Binder
    dotnet add package Microsoft.Extensions.Configuration.EnvironmentVariables
    dotnet add package Microsoft.Extensions.Configuration.Json
    dotnet add package Microsoft.Extensions.Configuration.UserSecrets

    dotnet add package Microsoft.Extensions.Logging.Json
    dotnet add package Microsoft.Extensions.Logging.Debug

    dotnet add package Azure.Identity
    ```
- Common code (`Internal` folder)
- Configuration defined

## Choose development path:
    
1. Agent and service type:
   - **ChatCompletion**
     - Open AI
     - Inference
   - **Azure Agent**        
     - New: Define and use a new agent.
     - Existing: Use the agent identifier.
2. Tooling
   - Use youe own plugin
   - Use demo plugin

## Configure

```sh
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "<model deployment name>"
dotnet user-secrets set "AzureOpenAI:Endpoint" "<endpoint>"
dotnet user-secrets set "AzureOpenAI:ApiKey" "<copy from portal>"
```

## Code

> NOTE: Type name conflicts: `Agent`, `AgentThread`

> Add NoWarn to project for SKEXP** (or #pragma)


#### Initialize

- `AIProjectClient` - Required for `AzureAIAgent` or when discovering AI Services via a project connection.
- `Kernel` - Required for `ChatCompletionAgent`

```csharp
ConnectionProperties aiConnection = await projectClient.GetConnectionAsync(ConnectionType.AzureOpenAI);

aiConnection.GetEndpoint()
aiConnection.GetApiKey()
```

#### Create the agent

AzureAIAgent needs either the identifier of an existing agent definition or to create a new definition.

#### Invoke the agent

This is the same for all agents.
Streaming also
AgentThread

#### Switch to `ChatConsole` (optional)

#### Add Plugin

## Multiagent

> Next Time!


---

# Outdoor Planner Agent

what is the best day and time to play tennis this week
will it rain on wednesday?
I'm thinking about a hike tomorrow
What's the outlook for snowboarding?
when swim
when golf
when bike
