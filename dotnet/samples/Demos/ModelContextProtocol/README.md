# Model Context Protocol Sample

This example demonstrates how to use Model Context Protocol tools with Semantic Kernel.

MCP is an open protocol that standardizes how applications provide context to LLMs.

For for information on Model Context Protocol (MCP) please refer to the [documentation](https://modelcontextprotocol.io/introduction).

This sample uses [mcpdotnet](https://www.nuget.org/packages/mcpdotnet) is heavily influenced by the [samples](https://github.com/PederHP/mcpdotnet/tree/main/samples) from that repository.

The sample shows:

1. How to connect to an MCP Server using [mcpdotnet](https://www.nuget.org/packages/mcpdotnet)
2. Retrieve the list of tools the MCP Server makes available
3. Convert the MCP tools to Semantic Kernel functions so they can be added to a Kernel instance
4. Invoke the tools from Semantic Kernel using function calling

## Configuring Secrets or Environment Variables

The example require credentials to access OpenAI.

If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### To set your secrets with Secret Manager

```text
cd dotnet/samples/Demos/ModelContextProtocol

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."
 "..."
```

### To set your secrets with environment variables

Use these names:

```text
# OpenAI
OpenAI__ChatModelId
OpenAI__ApiKey
```
