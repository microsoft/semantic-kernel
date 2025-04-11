# Semantic Kernel as MCP Server

This sample demonstrates how to expose your Semantic Kernel instance as an MCP (Model Context Protocol) server.

## Getting Started with Stdio

To run this sample using the `stdio` transport (default), set up your MCP host (like [Claude Desktop](https://claude.ai/download) or [VSCode GitHub Copilot Agents](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)) with the following configuration:

```json
{
    "mcpServers": {
        "sk": {
            "command": "uv",
            "args": [
                "--directory=<path to sk project>/semantic-kernel/python/samples/demos/sk_mcp_server",
                "run",
                "sk_mcp_server.py"
            ],
            "env": {
                "OPENAI_API_KEY": "<your_openai_api_key>",
                "OPENAI_CHAT_MODEL_ID": "gpt-4o-mini"
            }
        }
    }
}
```

Alternatively, you can run the server directly with the following command:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/sk_mcp_server run sk_mcp_server.py
```

## Getting Started with SSE

To run this sample as an SSE (Server-Sent Events) server, set the same environment variables as above and run the following command:

```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/sk_mcp_server run sk_mcp_server.py --transport sse --port 8000
```

This will start a server that listens for incoming requests on port `8000`.

---

In both cases, `uv` will ensure that `semantic-kernel` is installed with the `mcp` extra in a temporary virtual environment.

## Extending the sample

This sample creates two functions:

- `echo-echo_function`: A simple function that echoes back the input.
- `prompt-prompt`: a function that uses a Semantic Kernel prompt to generate a response.
