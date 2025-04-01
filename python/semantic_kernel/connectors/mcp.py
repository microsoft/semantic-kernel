# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import abstractmethod
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from functools import partial
from typing import Any

from mcp import ClientSession, McpError, StdioServerParameters, stdio_client
from mcp.client.sse import sse_client
from mcp.types import Tool
from pydantic import Field

from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError, ServiceInvalidTypeError
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)


class MCPClient(KernelBaseModel):
    """MCP server settings."""

    session: ClientSession | None = None

    @asynccontextmanager
    async def get_session(self):
        """Get or Open an MCP session."""
        try:
            if self.session is None:
                # If the session is not open, create always new one
                async with self.get_mcp_client() as (read, write), ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
            else:
                # If the session is set by the user, just yield it
                yield self.session
        except Exception as ex:
            raise KernelPluginInvalidConfigurationError("Failed establish MCP session.") from ex

    @abstractmethod
    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP client."""
        pass

    async def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Call a tool with the given arguments."""
        try:
            async with self.get_session() as session:
                return await session.call_tool(tool_name, arguments=kwargs)
        except McpError:
            raise
        except Exception as ex:
            raise FunctionExecutionException(f"Failed to call tool '{tool_name}'.") from ex


class MCPStdioClient(MCPClient):
    """MCP stdio client settings."""

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    encoding: str = "utf-8"

    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP stdio client."""
        return stdio_client(
            server=StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env,
                encoding=self.encoding,
            )
        )


class MCPSseClient(MCPClient):
    """MCP sse server settings."""

    url: str
    headers: dict[str, Any] | None = None
    timeout: float = 5
    sse_read_timeout: float = 60 * 5

    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP SSE client."""
        return sse_client(
            url=self.url,
            headers=self.headers,
            timeout=self.timeout,
            sse_read_timeout=self.sse_read_timeout,
        )


@experimental
def get_parameters_from_tool(tool: Tool) -> list[KernelParameterMetadata]:
    """Creates an MCPFunction instance from a tool."""
    properties = tool.inputSchema.get("properties", None)
    required = tool.inputSchema.get("required", None)
    # Check if 'properties' is missing or not a dictionary
    if properties is None or not isinstance(properties, dict):
        raise ServiceInvalidTypeError("""Could not parse tool properties,
            please ensure your server returns properties as a dictionary and required as an array.""")
    if required is None or not isinstance(required, list):
        raise ServiceInvalidTypeError("""Could not parse tool required fields,
            please ensure your server returns required as an array.""")
    return [
        KernelParameterMetadata(
            name=prop_name,
            is_required=prop_name in required,
            type=prop_details.get("type"),
            default_value=prop_details.get("default", None),
            schema_data=prop_details["items"]
            if "items" in prop_details and prop_details["items"] is not None and isinstance(prop_details["items"], dict)
            else {"type": f"{prop_details['type']}"}
            if "type" in prop_details
            else None,
        )
        for prop_name, prop_details in properties.items()
    ]


@experimental
async def create_plugin_from_mcp_server(plugin_name: str, description: str, client: MCPClient) -> KernelPlugin:
    """Creates a KernelPlugin from an MCP server.

    Args:
        plugin_name: The name of the plugin.
        description: The description of the plugin.
        client: The MCP client to use for communication, should be a StdioClient or SseClient.

    """
    async with client.get_session() as session:
        return KernelPlugin(
            name=plugin_name,
            description=description,
            functions=[
                KernelFunctionFromMethod(
                    method=kernel_function(name=tool.name, description=tool.description)(
                        partial(client.call_tool, tool.name)
                    ),
                    parameters=get_parameters_from_tool(tool),
                )
                for tool in (await session.list_tools()).tools
            ],
        )
