The server code and some of the agent code for this samples comes from: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers/simple-auth
in order to demonstrate connecting with OAuth to a MCP server with SK.

# MCP OAuth Authentication Demo

This example demonstrates OAuth 2.0 authentication with the Model Context Protocol using **separate Authorization Server (AS) and Resource Server (RS)** to comply with the new RFC 9728 specification.

---

## Running the Servers

### Step 1: Start Authorization Server

```bash
# Navigate to the simple-auth directory
cd samples/demos/mcp_with_oauth/server

# Start Authorization Server on port 9000
uv run mcp-simple-auth-as --port=9000
```

**What it provides:**

- OAuth 2.0 flows (registration, authorization, token exchange)
- Simple credential-based authentication (no external provider needed)  
- Token introspection endpoint for Resource Servers (`/introspect`)

---

### Step 2: Start Resource Server (MCP Server)

```bash
# In another terminal, navigate to the simple-auth directory
cd samples/demos/mcp_with_oauth/server

# Start Resource Server on port 8001, connected to Authorization Server
uv run mcp-simple-auth-rs --port=8001 --auth-server=http://localhost:9000  --transport=streamable-http

# With RFC 8707 strict resource validation (recommended for production)
uv run mcp-simple-auth-rs --port=8001 --auth-server=http://localhost:9000  --transport=streamable-http --oauth-strict

```

### Step 3: Test with Client

Either have Azure settings setup in your global venv, or add a `.env` file in `samples/demos/mcp_with_oauth/agent` with the following content:
```bash
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=
```

and then:

```bash
cd samples/demos/mcp_with_oauth
# Start agent with streamable HTTP plugin
uv --env-file .env run agent
```

or open file main.py in samples/demos/mcp_with_oauth/agent and run it in your IDE.

For more details on how the server and auth flows work, see https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers/simple-auth
