"""
Legacy Combined Authorization Server + Resource Server for MCP.

This server implements the old spec where MCP servers could act as both AS and RS.
Used for backwards compatibility testing with the new split AS/RS architecture.

NOTE: this is a simplified example for demonstration purposes.
This is not a production-ready implementation.

"""

import datetime
import logging
from typing import Any, Literal

import click
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions
from mcp.server.fastmcp.server import FastMCP
from pydantic import AnyHttpUrl, BaseModel
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from .simple_auth_provider import SimpleAuthSettings, SimpleOAuthProvider

logger = logging.getLogger(__name__)


class ServerSettings(BaseModel):
    """Settings for the simple auth MCP server."""

    # Server settings
    host: str = "localhost"
    port: int = 8000
    server_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")
    auth_callback_path: str = "http://localhost:8000/login/callback"


class LegacySimpleOAuthProvider(SimpleOAuthProvider):
    """Simple OAuth provider for legacy MCP server."""

    def __init__(self, auth_settings: SimpleAuthSettings, auth_callback_path: str, server_url: str):
        super().__init__(auth_settings, auth_callback_path, server_url)


def create_simple_mcp_server(server_settings: ServerSettings, auth_settings: SimpleAuthSettings) -> FastMCP:
    """Create a simple FastMCP server with simple authentication."""
    oauth_provider = LegacySimpleOAuthProvider(
        auth_settings, server_settings.auth_callback_path, str(server_settings.server_url)
    )

    mcp_auth_settings = AuthSettings(
        issuer_url=server_settings.server_url,
        client_registration_options=ClientRegistrationOptions(
            enabled=True,
            valid_scopes=[auth_settings.mcp_scope],
            default_scopes=[auth_settings.mcp_scope],
        ),
        required_scopes=[auth_settings.mcp_scope],
        # No resource_server_url parameter in legacy mode
        resource_server_url=None,
    )

    app = FastMCP(
        name="Simple Auth MCP Server",
        instructions="A simple MCP server with simple credential authentication",
        auth_server_provider=oauth_provider,
        host=server_settings.host,
        port=server_settings.port,
        debug=True,
        auth=mcp_auth_settings,
    )

    @app.custom_route("/login", methods=["GET"])
    async def login_page_handler(request: Request) -> Response:
        """Show login form."""
        state = request.query_params.get("state")
        if not state:
            raise HTTPException(400, "Missing state parameter")
        return await oauth_provider.get_login_page(state)

    @app.custom_route("/login/callback", methods=["POST"])
    async def login_callback_handler(request: Request) -> Response:
        """Handle simple authentication callback."""
        return await oauth_provider.handle_login_callback(request)

    @app.tool()
    async def get_time() -> dict[str, Any]:
        """
        Get the current server time.

        This tool demonstrates that system information can be protected
        by OAuth authentication. User must be authenticated to access it.
        """

        now = datetime.datetime.now()

        return {
            "current_time": now.isoformat(),
            "timezone": "UTC",  # Simplified for demo
            "timestamp": now.timestamp(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

    return app


@click.command()
@click.option("--port", default=8000, help="Port to listen on")
@click.option(
    "--transport",
    default="streamable-http",
    type=click.Choice(["sse", "streamable-http"]),
    help="Transport protocol to use ('sse' or 'streamable-http')",
)
def main(port: int, transport: Literal["sse", "streamable-http"]) -> int:
    """Run the simple auth MCP server."""
    logging.basicConfig(level=logging.INFO)

    auth_settings = SimpleAuthSettings()
    # Create server settings
    host = "localhost"
    server_url = f"http://{host}:{port}"
    server_settings = ServerSettings(
        host=host,
        port=port,
        server_url=AnyHttpUrl(server_url),
        auth_callback_path=f"{server_url}/login",
    )

    mcp_server = create_simple_mcp_server(server_settings, auth_settings)
    logger.info(f"🚀 MCP Legacy Server running on {server_url}")
    mcp_server.run(transport=transport)
    return 0


if __name__ == "__main__":
    main()  # type: ignore[call-arg]
