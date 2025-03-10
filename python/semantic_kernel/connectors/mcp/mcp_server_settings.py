# Copyright (c) Microsoft. All rights reserved.
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

from semantic_kernel.kernel_pydantic import KernelBaseModel


class MCPServerSettings(KernelBaseModel):
    """MCP server settings."""

    session: ClientSession | None = None
    exit_stack: AsyncExitStack = AsyncExitStack()

    async def initialize_session(self):
        """Initialize the MCP session."""
        if self.session is not None:
            return self.session
        # Get the MCP client and initialize the session.
        client = self._get_mcp_client()
        # Use the exit stack to manage the client and session.
        read, write = await self.exit_stack.enter_async_context(client)
        self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        # Initialize the session.
        await self.session.initialize()
        return None

    def _get_mcp_client(self):
        """Get an MCP client."""
        raise NotImplementedError("This method should be implemented by subclasses")


class MCPStdioServerSettings(MCPServerSettings):
    """MCP stdio server settings."""

    server_params: StdioServerParameters

    def _get_mcp_client(self):
        return stdio_client(server=self.server_params)


class MCPSseServerSettings(MCPServerSettings):
    """MCP sse server settings."""

    url: str

    def _get_mcp_client(self):
        return sse_client(url=self.url)
