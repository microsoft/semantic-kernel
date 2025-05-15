# Semantic Kernel and MCP

This sample demonstrates how to:

- Expose your Semantic Kernel instance or an Agent as an MCP (Model Context Protocol) server;
- Use your Semantic Kernel instance as an MCP host to consume MCP servers.

## Getting Started

### Semantic Kernel Agent as an MCP Server

#### Getting Started with Stdio

To run these samples using the `stdio` transport (default), set up your MCP host (like [Claude Desktop](https://claude.ai/download) or [VSCode GitHub Copilot Agents](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)) with the following configuration:

```json
{
  "mcpServers": {
    "sk": {
      "command": "uv",
      "args": [
        "--directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server",
        "run",
        "sk_mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "<your_openai_api_key>",
        "OPENAI_CHAT_MODEL_ID": "gpt-4o-mini"
      }
    },
    "agent": {
      "command": "uv",
      "args": [
        "--directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server",
        "run",
        "agent_mcp_server.py"
      ],
      "env": {
        "AZURE_AI_AGENT_PROJECT_CONNECTION_STRING": "<your azure connection string>",
        "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME": "<your azure model deployment name>"
      }
    }
  }
}
```

Alternatively, you can run the server directly with the following command:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run sk_mcp_server.py
```

or:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run agent_mcp_server.py
```

#### Getting Started with SSE

To run these samples as an SSE (Server-Sent Events) server, set the same environment variables as above and run the following command:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run sk_mcp_server.py --transport sse --port 8000
```

or:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run agent_mcp_server.py --transport sse --port 8000
```

This will start a server that listens for incoming requests on port `8000`.

---

In both cases, `uv` will ensure that `semantic-kernel` is installed with the `mcp` extra in a temporary virtual environment.

#### Extending the sample

The _sk_mcp_server_ sample creates two functions:

- `echo-echo_function`: A simple function that echoes back the input.
- `prompt-prompt`: a function that uses a Semantic Kernel prompt to generate a response.

The _agent_mcp_server_ sample creates a simple agent that uses the Azure OpenAI service to generate a response.
It exposes a single function:

- `mcp-host`: A function that uses the Azure OpenAI service to generate a response.

Once the server is created, you get a `mcp.server.lowlevel.Server` object, which you can then extend to add further functionality, like resources or prompts.

### Semantic Kernel as an MCP host

#### Getting Started with Stdio

The `sk_as_mcp_host.py` sample connects to the MCP server from `sk_mcp_server.py` sample with stdio transport by default:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run sk_as_mcp_host.py
```

Optionally, you can connect to a remote MCP server with SSE transport (e.g. `http://localhost:<port>` from the `sk_mcp_server.py`):

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run sk_as_mcp_host.py --transport sse --url <your_server_url>
```
