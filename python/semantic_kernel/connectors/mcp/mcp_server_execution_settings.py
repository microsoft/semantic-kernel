# Copyright (c) Microsoft. All rights reserved.
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class MCPServerExecutionSettings(KernelBaseModel):
    """MCP server settings."""

    session: ClientSession | None = None

    @asynccontextmanager
    async def get_session(self):
        """Get or Open an MCP session."""
        if self.session is None:
            # If the session is not open, create always new one
            async with self.get_mcp_client() as (read, write), ClientSession(read, write) as session:
                await session.initialize()
                yield session
        else:
            # If the session is already open by the user, just yield it
            yield self.session

    def get_mcp_client(self):
        """Get an MCP client."""
        raise NotImplementedError("This method is only needed for subclasses.")


class MCPStdioServerExecutionSettings(MCPServerExecutionSettings):
    """MCP stdio server settings."""

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    encoding: str = "utf-8"

    def get_mcp_client(self):
        """Get an MCP stdio client."""
        return stdio_client(
            server=StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env,
                encoding=self.encoding,
            )
        )


class MCPSseServerExecutionSettings(MCPServerExecutionSettings):
    """MCP sse server settings."""

    url: str
    headers: dict[str, Any] | None = None
    timeout: float = 5
    sse_read_timeout: float = 60 * 5

    def get_mcp_client(self):
        """Get an MCP SSE client."""
        return sse_client(
            url=self.url,
            headers=self.headers,
            timeout=self.timeout,
            sse_read_timeout=self.sse_read_timeout,
        )
