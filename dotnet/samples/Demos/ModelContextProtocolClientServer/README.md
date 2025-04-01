# Model Context Protocol Client Server Sample

This sample demonstrates how to use Semantic Kernel with the [Model Context Protocol (MCP) C# SDK](https://github.com/modelcontextprotocol/csharp-sdk) to build an MCP server and client.

MCP is an open protocol that standardizes how applications provide context to LLMs. Please refer to the [documentation](https://modelcontextprotocol.io/introduction) for more information.

The sample shows:

1. How to create an MCP server powered by SK: SK plugins are exposed as MCP tools.    
2. How to create an MCP client and import the MCP tools to SK and use them.

## Configuring Secrets or Environment Variables

The example require credentials to access OpenAI.

If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### Set Secrets with Secret Manager

```text
cd dotnet/samples/Demos/ModelContextProtocolClientServer/MCPClient

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."
 "..."
```

### Set Secrets with Environment Variables

Use these names:

```text
# OpenAI
OpenAI__ChatModelId
OpenAI__ApiKey
```

## Run the Sample

To run the sample, follow these steps:
1. Right-click on the `MCPClient` project in Visual Studio and select `Set as Startup Project`.  
2. Press `F5` to run the project.