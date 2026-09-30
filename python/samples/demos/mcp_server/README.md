# Semantic Kernel as MCP Server

This sample demonstrates how to expose your Semantic Kernel instance or a Agent as an MCP (Model Context Protocol) server.

## Getting Started with Stdio

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
                "AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME": "<your azure model deployment name>",
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

## Getting Started with SSE

To run these samples as an SSE (Server-Sent Events) server, set the same environment variables as above and run the following command:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run sk_mcp_server.py --transport sse --port 8000
```
or:
```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server run agent_mcp_server.py --transport sse --port 8000
```

This will start a server that listens for incoming requests on port `8000`.

> [!NOTE]
> By default the SSE server binds to `127.0.0.1` (loopback) and only accepts requests
> with a loopback `Host` header and, when present, a loopback `Origin` header. A local
> MCP server exposes tools, plugins and model providers backed by your own credentials,
> so it is good practice to keep it reachable only from your own machine. The
> [MCP specification](https://modelcontextprotocol.io/) recommends validating `Origin`
> and binding to loopback, in part to guard against [DNS rebinding](https://en.wikipedia.org/wiki/DNS_rebinding).
>
> You can override the bind address with `--host`, e.g. `--host 0.0.0.0` to expose the
> server on the network. Do this only on a trusted network. The bundled Host/Origin
> checks only allow loopback callers, so a non-loopback deployment needs proper
> authentication - see the [`mcp_with_oauth`](../mcp_with_oauth/) sample for the
> authenticated, Streamable-HTTP pattern recommended for production.

---

In both cases, `uv` will ensure that `semantic-kernel` is installed with the `mcp` extra in a temporary virtual environment.

## Extending the sample

The *sk_mcp_server* sample creates two functions:

- `echo_function`: A simple function that echoes back the input.
- `prompt`: a function that uses a Semantic Kernel prompt to generate a response.

The *agent_mcp_server* sample creates a simple agent that uses the Azure OpenAI service to generate a response.
It exposes a single function:

- `Host`: A function that uses the Azure OpenAI service to generate a response.

Once the server is created, you get a `mcp.server.lowlevel.Server` object, which you can then extend to add further functionality, like resources or prompts. 

## Tool names

By default, tools use bare function names. When functions in different plugins have the same
name, the server exposes the first function and logs a warning for each skipped duplicate.
Discovery and invocation use the same retained function.

To expose both functions, enable plugin-qualified names:

```python
server = kernel.as_mcp_server(use_plugin_names=True)
```

For example, the sample's tools become `echo-echo_function` and `prompt-prompt`.
The option is also available on `create_mcp_server_from_kernel`,
`create_mcp_server_from_functions`, and `Agent.as_mcp_server`.
Tool names longer than MCP's recommended 128 characters are exposed with a warning.
Clients may impose stricter name-length limits.
Enabling the option changes public tool names, so existing callers must use the new names.
The `excluded_functions` option continues to use bare function names in either mode.
