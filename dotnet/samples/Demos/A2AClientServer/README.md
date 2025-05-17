# A2A Client and Server samples

> **Warning**
> The [A2A protocol](https://google.github.io/A2A/) is still under development and changing fast.
> We will try to keep these samples updated as the protocol evolves.

These samples are built with [SharpA2A.Core](https://www.nuget.org/packages/SharpA2A.Core) and demonstrate:

1. Creating an A2A Server which exposes multiple agents using the A2A protocol.
2. Creating an A2A Client with a command line interface which invokes agents using the A2A protocol.

## Configuring Secrets or Environment Variables

The samples can be configured to use chat completion agents or Azure AI agents.

### Configuring for use with Chat Completion Agents

Provide your OpenAI API key via .Net secrets

```bash
dotnet user-secrets set "A2AClient:ApiKey" "..."
```

Optionally if you want to use chat completion agents in the server then set the OpenAI key for the server to use.

```bash
dotnet user-secrets set "A2AServer:ApiKey" "..."
```

### Configuring for use with Azure AI Agents

You must create the agents in an Azure AI Foundry project and then provide the connection string and agents ids

```bash
dotnet user-secrets set "A2AServer:ConnectionString" "..."
dotnet user-secrets set "A2AServer:InvoiceAgentId" "..."
dotnet user-secrets set "A2AServer:PolicyA:qgentId" "..."
dotnet user-secrets set "A2AServer:LogisticsAgentId" "..."
```

### Configuring Agents for the A2A Client

The A2A client will connect to remote agents using the A2A protocol.

By default the client will connect to the invoice, policy and logistics agents provided by the sample A2A Server.

These are available at the following URL's:

- http://localhost:5000/policy/ 
- http://localhost:5000/invoice/ 
- http://localhost:5000/logistics/

if you want to change which agents are using then set the agents url's as a space delimited string as follows:

```bash
dotnet user-secrets set "A2AClient:AgentUrls" "http://localhost:5000/policy/ http://localhost:5000/invoice/ http://localhost:5000/logistics/"
```

## Run the Sample

To run the sample, follow these steps:

1. Run the A2A server:
    ```bash
    cd A2AServer
    dotnet run
    ```  
2. Run the A2A client:
    ```bash
    cd A2AClient
    dotnet run
    ```  
3. Enter your request e.g. "Customer is disputing transaction TICKET-XYZ987 as they claim the received fewer t-shirts than ordered."