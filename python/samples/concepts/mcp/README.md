# Model Context Protocol

The model context protocol is a standard created by Anthropic to allow models to share context with each other. See the [official documentation](https://modelcontextprotocol.io/introduction) for more information.

It consists of clients and servers, and servers can be hosted locally, or they can be exposed as a online API.

Our goal is that Semantic Kernel can act as both a client and a server.

In this folder the client side of things is demonstrated. It takes the definition of a server and uses that to create a Semantic Kernel plugin, this plugin exposes the tools and prompts of the server as functions in the kernel.

Those can then be used with function calling in a chat or agent.

## Server types

There are two types of servers, Stdio and Sse based. The sample shows how to use the Stdio based server, which get's run locally, in this case by using [npx](https://docs.npmjs.com/cli/v8/commands/npx).

Some other common runners are [uvx](https://docs.astral.sh/uv/guides/tools/), for python servers and [docker](https://www.docker.com/), for containerized servers.

The code shown works the same for a Sse server, only then a MCPSsePlugin needs to be used instead of the MCPStdioPlugin.

The reverse, using Semantic Kernel as a server, is not yet implemented, but will be in the future.

## Running the sample

1. Make sure you have the [Node.js](https://nodejs.org/en/download/) installed.
2. Make sure you have the [npx](https://docs.npmjs.com/cli/v8/commands/npx) available in PATH.
3. The Github MCP Server uses a Github Personal Access Token (PAT) to authenticate, see [the documentation](https://github.com/modelcontextprotocol/servers/tree/main/src/github) on how to create one.
4. Install Semantic Kernel with the mcp extra:

```bash
pip install semantic-kernel[mcp]
```

5. Run the sample:

```bash
cd python/samples/concepts/mcp
python mcp_as_plugin.py
```

or:

```bash
cd python/samples/concepts/mcp
python agent_with_mcp_plugin.py
```
