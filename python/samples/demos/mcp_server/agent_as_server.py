# /// script # noqa: CPY001
# dependencies = [
#   "semantic-kernel[mcp]",
# ]
# ///
# Copyright (c) Microsoft. All rights reserved.
import argparse
import ipaddress
import logging
from typing import Annotated, Any, Literal

import anyio
from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)

"""
This sample demonstrates how to expose an Agent as a MCP server.

To run this sample, set up your MCP host (like Claude Desktop or VSCode Github Copilot Agents)
with the following configuration:
```json
{
    "mcpServers": {
        "sk": {
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
Alternatively, you can run this as a SSE server, by setting the same environment variables as above, 
and running the following command:
```bash
uv --directory=<path to sk project>/semantic-kernel/python/samples/demos/mcp_server \
run agent_mcp_server.py --transport sse --port 8000
```
This will start a server that listens for incoming requests on port 8000.

In both cases, uv will make sure to install semantic-kernel with the mcp extra for you in a temporary venv.
"""


def is_loopback_host(host: str) -> bool:
    """Return True if the host refers to a loopback interface (incl. IPv6 ::1)."""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run the Semantic Kernel MCP server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["sse", "stdio"],
        default="stdio",
        help="Transport method to use (default: stdio).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to use for SSE transport (required if transport is 'sse').",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help=(
            "Host/interface to bind the SSE server to (default: 127.0.0.1). "
            "Binding to anything other than loopback (e.g. 0.0.0.0) exposes the server "
            "to the network and should only be done on a trusted network with authentication added."
        ),
    )
    args = parser.parse_args()
    if args.transport == "sse" and args.port is None:
        parser.error("--port is required when --transport is 'sse'.")
    return args


# Define a simple plugin for the sample
class MenuPlugin:
    """A sample Menu Plugin used for the sample."""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"


async def run(transport: Literal["sse", "stdio"] = "stdio", port: int | None = None, host: str = "127.0.0.1") -> None:
    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        agent = AzureAIAgent(
            client=client,
            definition=await client.agents.create_agent(
                model=AzureAIAgentSettings().model_deployment_name,
                name="Host",
                instructions="Answer questions about the menu.",
            ),
            plugins=[MenuPlugin()],  # add the sample plugin to the agent
        )
        server = agent.as_mcp_server()

        if transport == "sse" and port is not None:
            import nest_asyncio
            import uvicorn
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.middleware import Middleware
            from starlette.middleware.trustedhost import TrustedHostMiddleware
            from starlette.responses import PlainTextResponse
            from starlette.routing import Mount, Route
            from starlette.types import ASGIApp, Receive, Scope, Send

            # A local MCP server is a security boundary, not a generic web server: it exposes
            # tools, plugins and model providers backed by the developer's credentials. Without
            # Host/Origin validation a malicious web page could use DNS rebinding to reach this
            # loopback listener from the victim's browser and invoke the exposed MCP tools.
            # The MCP spec therefore requires servers to validate Origin and bind to loopback.
            allowed_hosts = [
                "localhost",
                "127.0.0.1",
                "[::1]",
                f"localhost:{port}",
                f"127.0.0.1:{port}",
                f"[::1]:{port}",
            ]
            allowed_origins = {
                "http://localhost",
                "http://127.0.0.1",
                "http://[::1]",
                f"http://localhost:{port}",
                f"http://127.0.0.1:{port}",
                f"http://[::1]:{port}",
            }

            class OriginValidationMiddleware:
                """Reject requests with an untrusted Origin header (DNS-rebinding defense)."""

                def __init__(self, app: ASGIApp) -> None:
                    self.app = app

                async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
                    if scope["type"] == "http":
                        origin = dict(scope["headers"]).get(b"origin")
                        if origin is not None:
                            try:
                                origin_value = origin.decode("ascii")
                            except UnicodeDecodeError:
                                origin_value = None
                            if origin_value not in allowed_origins:
                                response = PlainTextResponse("Forbidden: invalid Origin header", status_code=403)
                                await response(scope, receive, send)
                                return
                    await self.app(scope, receive, send)

            sse = SseServerTransport("/messages/")

            async def handle_sse(request):
                async with sse.connect_sse(request.scope, request.receive, request._send) as (
                    read_stream,
                    write_stream,
                ):
                    await server.run(read_stream, write_stream, server.create_initialization_options())

            starlette_app = Starlette(
                debug=False,
                routes=[
                    Route("/sse", endpoint=handle_sse),
                    Mount("/messages/", app=sse.handle_post_message),
                ],
                middleware=[
                    Middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts),
                    Middleware(OriginValidationMiddleware),
                ],
            )

            if not is_loopback_host(host):
                logger.warning(
                    "Binding the MCP SSE server to %s exposes it beyond loopback. The bundled Host/Origin "
                    "checks only allow loopback callers; for a network-reachable or credentialed deployment "
                    "add proper authentication (see the mcp_with_oauth sample) before doing this.",
                    host,
                )

            nest_asyncio.apply()
            uvicorn.run(starlette_app, host=host, port=port)  # nosec
        elif transport == "stdio":
            from mcp.server.stdio import stdio_server

            async def handle_stdin(stdin: Any | None = None, stdout: Any | None = None) -> None:
                async with stdio_server() as (read_stream, write_stream):
                    await server.run(read_stream, write_stream, server.create_initialization_options())

            await handle_stdin()


if __name__ == "__main__":
    args = parse_arguments()
    anyio.run(run, args.transport, args.port, args.host)
