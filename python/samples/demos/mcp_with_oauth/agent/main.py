# Copyright (c) Microsoft. All rights reserved.

import asyncio
import threading
import time
import webbrowser
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin

"""
The following sample demonstrates how to setup a MCP Server that uses OAuth 2.0 for authentication.

It requires a a couple of extra classes, in order to run a server that can handle the oauth callback.
When connecting to a existing Oauth server this should be simpler.

Most of the code for the auth comes from: 
https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers/simple-auth

The actual MCP server exposes a single tool, called get_time, which is what the input asks for.
See server/mcp_simple_auth/server.py for details.

Follow the readme in the root of this demo for instructions on how to run.
"""


# Simulate a conversation with the agent
USER_INPUTS = ["What time is it?"]


class InMemoryTokenStorage(TokenStorage):
    """Simple in-memory token storage implementation."""

    def __init__(self):
        self._tokens: OAuthToken | None = None
        self._client_info: OAuthClientInformationFull | None = None

    async def get_tokens(self) -> OAuthToken | None:
        return self._tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._client_info = client_info


class CallbackHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler to capture OAuth callback."""

    def __init__(self, request, client_address, server, callback_data):
        """Initialize with callback data storage."""
        self.callback_data = callback_data
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)

        if "code" in query_params:
            self.callback_data["authorization_code"] = query_params["code"][0]
            self.callback_data["state"] = query_params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>setTimeout(() => window.close(), 2000);</script>
            </body>
            </html>
            """)
        elif "error" in query_params:
            self.callback_data["error"] = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
            <html>
            <body>
                <h1>Authorization Failed</h1>
                <p>Error: {query_params["error"][0]}</p>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """.encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class CallbackServer:
    """Simple server to handle OAuth callbacks."""

    def __init__(self, port=3000):
        self.port = port
        self.server = None
        self.thread = None
        self.callback_data = {"authorization_code": None, "state": None, "error": None}

    def _create_handler_with_data(self):
        """Create a handler class with access to callback data."""
        callback_data = self.callback_data

        class DataCallbackHandler(CallbackHandler):
            def __init__(self, request, client_address, server):
                super().__init__(request, client_address, server, callback_data)

        return DataCallbackHandler

    def start(self):
        """Start the callback server in a background thread."""
        handler_class = self._create_handler_with_data()
        self.server = HTTPServer(("localhost", self.port), handler_class)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"🖥️  Started callback server on http://localhost:{self.port}")

    def stop(self):
        """Stop the callback server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)

    def wait_for_callback(self, timeout=300):
        """Wait for OAuth callback with timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.callback_data["authorization_code"]:
                return self.callback_data["authorization_code"]
            if self.callback_data["error"]:
                raise Exception(f"OAuth error: {self.callback_data['error']}")
            time.sleep(0.1)
        raise Exception("Timeout waiting for OAuth callback")

    def get_state(self):
        """Get the received state parameter."""
        return self.callback_data["state"]


async def main():
    # 1. Create the agent
    callback_server = CallbackServer(port=3030)
    callback_server.start()

    async def callback_handler() -> tuple[str, str | None]:
        """Wait for OAuth callback and return auth code and state."""
        print("⏳ Waiting for authorization callback...")
        try:
            auth_code = callback_server.wait_for_callback(timeout=300)
            return auth_code, callback_server.get_state()
        finally:
            callback_server.stop()

    client_metadata_dict = {
        "client_name": "Simple Auth Client",
        "redirect_uris": ["http://localhost:3030/callback"],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_post",
    }

    async def _default_redirect_handler(authorization_url: str) -> None:
        """Default redirect handler that opens the URL in a browser."""
        print(f"Opening browser for authorization: {authorization_url}")
        webbrowser.open(authorization_url)

    # Create OAuth authentication handler using the new interface
    oauth_auth = OAuthClientProvider(
        server_url="http://localhost:9000",
        client_metadata=OAuthClientMetadata.model_validate(client_metadata_dict),
        storage=InMemoryTokenStorage(),
        redirect_handler=_default_redirect_handler,
        callback_handler=callback_handler,
    )

    async with MCPStreamableHttpPlugin(
        name="AuthServer",
        description="Auth Server Plugin",
        url="http://localhost:8001/mcp",
        auth=oauth_auth,
        timeout=timedelta(seconds=60),
    ) as oath_plugin:
        agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name="ProtectedAgent",
            instructions="Answer the users questions.",
            plugins=[oath_plugin],
        )

        for user_input in USER_INPUTS:
            # 2. Create a thread to hold the conversation
            # If no thread is provided, a new thread will be
            # created and returned with the initial response
            thread: ChatHistoryAgentThread | None = None

            print(f"# User: {user_input}")
            # 3. Invoke the agent for a response
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response} ")
            thread = response.thread

            # 4. Cleanup: Clear the thread
            await thread.delete() if thread else None


"""
Expected output:
🖥️  Started callback server on http://localhost:3030
Opening browser for authorization: http://localhost:9000/authorize?response_type...
⏳ Waiting for authorization callback...
# User: What time is it?
# ProtectedAgent: The current time is 16:54:55 (4:54 PM) on July 10, 2025, in the UTC timezone. 
"""


def cli():
    """Entry point for UV script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()
