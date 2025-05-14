# A2A Client and Server samples

> **Warning**
> The [A2A protocol](https://google.github.io/A2A/) is still under development and changing fast.
> We will try to keep these samples updated as the protocol evolves.

These samples are built with [SharpA2A.Core](https://www.nuget.org/packages/SharpA2A.Core) and demonstrate:

1. Creating an A2A Server which exposes multiple agents using the A2A protocol.
2. Creating an A2A Client with a command line interface which invokes agents using the A2A protocol.

## Configuring Secrets or Environment Variables

The samples require an OpenAI API key.

Create an environment variable need `OPENAI_API_KEY` with your OpenAI API key.


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
3. Enter your request e.g. "Show me all invoices for Contoso?"