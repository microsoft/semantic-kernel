# Model Context Protocol Client Server Samples

These samples use the [Model Context Protocol (MCP) C# SDK](https://github.com/modelcontextprotocol/csharp-sdk) and show:
1. How to create an MCP server powered by SK:
    - Expose SK plugins as MCP tools.
    - Expose SK prompt templates as MCP prompts.
    - Use Kernel Function as MCP `Read` resource handlers.
    - Use Kernel Function as MCP `Read` resource template handlers.

2. How a hosting app can use MCP client and SK:

    - Import MCP tools as SK functions and utilize them via the Chat Completion service.
    - Use MCP prompts as additional context for prompting.
    - Use MCP resources and resource templates as additional context for prompting.
    - Intercept and handle sampling requests from the MCP server in human-in-the-loop scenarios.
    - Import MCP tools as SK functions and utilize them via Chat Completion and Azure AI agents.

Please refer to the [MCP introduction](https://modelcontextprotocol.io/introduction) to get familiar with the protocol.
 
## Configuring Secrets or Environment Variables

The samples require credentials and other secrets to access AI models. If you have set up those credentials as secrets within Secret Manager or through environment variables for other samples from the solution in which this project is found, they will be re-used.

### Set Secrets with Secret Manager

```text
cd dotnet/samples/Demos/ModelContextProtocolClientServer/MCPClient

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."
dotnet user-secrets set "AzureAI:ConnectionString" "..."
dotnet user-secrets set "AzureAI:ChatModelId" "..."
 
```

### Set Secrets with Environment Variables

Use these names:

```text
# OpenAI
OpenAI__ChatModelId
OpenAI__ApiKey
AzureAI__ConnectionString
AzureAI__ChatModelId
```

## Run the Sample

To run the sample, follow these steps:

1. Right-click on the `MCPClient` project in Visual Studio and select `Set as Startup Project`.  
2. Press `F5` to run the project.
3. All samples will be executed sequentially. You can find the output in the console window.
4. You can run individual samples by commenting out the other samples in the `Main` method of the `Program.cs` file of the `MCPClient` project.

## Use MCP Inspector and Claude desktop app to access the MCP server

Both the MCP Inspector and the Claude desktop app can be used to access MCP servers for exploring and testing MCP server capabilities: tools, prompts, resources, etc.

### MCP Inspector

To use the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) follow these steps:

1. Open a terminal in the MCPServer project directory.
2. Run the `npx @modelcontextprotocol/inspector dotnet run` command to start the MCP Inspector. Make sure you have [node.js](https://nodejs.org/en/download/) and npm installed
   ```bash
   npx @modelcontextprotocol/inspector dotnet run
   ```
3. When the inspector is running, it will display a URL in the terminal, like this:
   ```
   MCP Inspector is up and running at http://127.0.0.1:6274
   ```
4. Open a web browser and navigate to the URL displayed in the terminal. This will open the MCP Inspector interface.
5. Find and click the "Connect" button in the MCP Inspector interface to connect to the MCP server.
6. As soon as the connection is established, you will see a list of available tools, prompts, and resources in the MCP Inspector interface.

### Claude Desktop App

To use the [Claude desktop app](https://claude.ai/) to access the MCP server, follow these steps:

1. 1. Download and install the app from the [Claude website](https://claude.ai/download).
2. In the app, go to File->Settings->Developer->Edit Config.
3. Open the `claude_desktop_config.json` file in a text editor and add the following configuration to the file:
   ```Json
   {
       "mcpServers": {
           "demo_mcp_server": {
               "command": "<Path to SK repo>/dotnet/samples/Demos/ModelContextProtocolClientServer/MCPServer/bin/Debug/net8.0/MCPServer.exe",
               "args": []
           }
       }
   }
   ```
4. Save the file and restart the app.

## Debugging the MCP Server  
   
To debug the MCP server in Visual Studio, follow these steps:  

1. Connect to the MCP server using either the MCP Inspector or the Claude desktop app. This should start the MCP server process.  
2. Set breakpoints in the MCP server code where you want to debug.  
3. In Visual Studio, go to `Debug` -> `Attach to Process`.  
4. In the `Attach to Process` dialog, find the `MCPServer.exe` process and select it.  
5. Click `Attach` to attach the debugger to the process.  
6. Once the debugger is attached, access the MCP server tools, prompts, or resources using the MCP Inspector or the Claude desktop app. 
   This will trigger the breakpoints you set in the MCP server code.

## Remote MCP Server

The MCP specification supports remote MCP servers. You can find more information at the following links:
 [Server-Side Events (SSE)](https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse) and [HTTP with SSE](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports#http-with-sse).
   
The [MCP C# SDK](https://github.com/modelcontextprotocol/csharp-sdk) provides all the necessary components to easily create a remote MCP server.
To get started, follow this sample: [AspNetCoreSseServer](https://github.com/modelcontextprotocol/csharp-sdk/tree/main/samples/AspNetCoreSseServer).

## Authentication

While details of native support for OAuth 2.1 are [still being discussed](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/284), you can consider a solution based on APIM 
acting as an [AI Gateway](https://github.com/Azure-Samples/AI-Gateway). This approach is demonstrated by the sample: [Secure Remote Microsoft Graph MCP Servers using Azure API Management (Experimental)](https://github.com/Azure-Samples/remote-mcp-apim-appservice-dotnet).