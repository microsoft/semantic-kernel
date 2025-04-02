# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import abstractmethod
from collections.abc import AsyncGenerator
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from functools import partial
from typing import Any

from mcp import McpError
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import CallToolResult, EmbeddedResource, Prompt, PromptMessage, TextResourceContents, Tool
from mcp.types import (
    ImageContent as MCPImageContent,
)
from mcp.types import (
    TextContent as MCPTextContent,
)
from pydantic import BaseModel, ConfigDict, Field

from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)


def mcp_prompt_message_to_semantic_kernel_type(
    mcp_type: PromptMessage,
) -> ChatMessageContent:
    """Convert a MCP container type to a Semantic Kernel type."""
    return ChatMessageContent(
        role=AuthorRole(mcp_type.role),
        items=[mcp_type_to_semantic_kernel_type(mcp_type.content)],
        inner_content=mcp_type,
    )


def mcp_call_tool_result_to_semantic_kernel_type(
    mcp_type: CallToolResult,
) -> list[TextContent | ImageContent | BinaryContent]:
    """Convert a MCP container type to a Semantic Kernel type."""
    return [mcp_type_to_semantic_kernel_type(item) for item in mcp_type.content]


def mcp_type_to_semantic_kernel_type(
    mcp_type: MCPImageContent | MCPTextContent | EmbeddedResource,
) -> TextContent | ImageContent | BinaryContent:
    """Convert a MCP type to a Semantic Kernel type."""
    if isinstance(mcp_type, MCPTextContent):
        return TextContent(text=mcp_type.text, inner_content=mcp_type)
    if isinstance(mcp_type, MCPImageContent):
        return ImageContent(data=mcp_type.data, mime_type=mcp_type.mimeType, inner_content=mcp_type)

    if isinstance(mcp_type.resource, TextResourceContents):
        return TextContent(
            text=mcp_type.resource.text,
            inner_content=mcp_type,
            metadata=mcp_type.annotations.model_dump() if mcp_type.annotations else {},
        )
    return BinaryContent(
        data=mcp_type.resource.blob,
        inner_content=mcp_type,
        metadata=mcp_type.annotations.model_dump() if mcp_type.annotations else {},
    )


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, validate_assignment=True, extra="allow"
    )

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

    async def call_tool(self, tool_name: str, **kwargs: Any) -> list[TextContent | ImageContent | BinaryContent]:
        """Call a tool with the given arguments."""
        try:
            async with self.get_session() as session:
                return mcp_call_tool_result_to_semantic_kernel_type(
                    await session.call_tool(tool_name, arguments=kwargs)
                )
        except McpError:
            raise
        except Exception as ex:
            raise FunctionExecutionException(f"Failed to call tool '{tool_name}'.") from ex

    async def get_prompt(self, prompt_name: str, **kwargs: Any) -> list[ChatMessageContent]:
        """Call a prompt with the given arguments."""
        try:
            async with self.get_session() as session:
                prompt_result = await session.get_prompt(prompt_name, arguments=kwargs)
                return [mcp_prompt_message_to_semantic_kernel_type(message) for message in prompt_result.messages]
        except McpError:
            raise
        except Exception as ex:
            raise FunctionExecutionException(f"Failed to call prompt '{prompt_name}'.") from ex


class MCPStdioServerConfig(MCPServerConfig):
    """MCP stdio server configuration.

    The arguments are used to create a StdioServerParameters object.
    Which is then used to create a stdio client.
    see mcp.client.stdio.stdio_client and mcp.client.stdio.stdio_server_parameters
    for more details.

    Any extra arguments passed to the constructor will be passed to the
    StdioServerParameters constructor.

    Args:
        command: The command to run the MCP server.
        args: The arguments to pass to the command.
        env: The environment variables to set for the command.
        encoding: The encoding to use for the command output.

    """

    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    encoding: str | None = None

    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP stdio client."""
        args = {
            "command": self.command,
            "args": self.args,
            "env": self.env,
        }
        if self.encoding:
            args["encoding"] = self.encoding
        if self.model_extra:
            args.update(self.model_extra)
        return stdio_client(server=StdioServerParameters(**args))


class MCPSseServerConfig(MCPServerConfig):
    """MCP sse server configuration.

    The arguments are used to create a sse client.
    see mcp.client.sse.sse_client for more details.

    Any extra arguments passed to the constructor will be passed to the
    sse client constructor.

    Args:
        url: The URL of the MCP server.
        headers: The headers to send with the request.
        timeout: The timeout for the request.
        sse_read_timeout: The timeout for reading from the SSE stream.

    """

    url: str
    headers: dict[str, Any] | None = None
    timeout: float | None = None
    sse_read_timeout: float | None = None

    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP SSE client."""
        args: dict[str, Any] = {
            "url": self.url,
        }
        if self.headers:
            args["headers"] = self.headers
        if self.timeout is not None:
            args["timeout"] = self.timeout
        if self.sse_read_timeout is not None:
            args["sse_read_timeout"] = self.sse_read_timeout
        if self.model_extra:
            args.update(self.model_extra)
        return sse_client(**args)


@experimental
def get_parameter_from_mcp_prompt(prompt: Prompt) -> list[KernelParameterMetadata]:
    """Creates a MCPFunction instance from a prompt."""
    # Check if 'properties' is missing or not a dictionary
    if not prompt.arguments:
        return []
    return [
        KernelParameterMetadata(
            name=prompt_argument.name,
            description=prompt_argument.description,
            is_required=True,
            type_object=str,
        )
        for prompt_argument in prompt.arguments
    ]


@experimental
def get_parameters_from_mcp_tool(tool: Tool) -> list[KernelParameterMetadata]:
    """Creates an MCPFunction instance from a tool."""
    properties = tool.inputSchema.get("properties", None)
    required = tool.inputSchema.get("required", None)
    # Check if 'properties' is missing or not a dictionary
    if not properties:
        return []
    return [
        KernelParameterMetadata(
            name=prop_name,
            is_required=prop_name in required,
            type=prop_details.get("type"),
            default_value=prop_details.get("default", None),
            schema_data=prop_details,
        )
        for prop_name, prop_details in properties.items()
    ]


@experimental
async def create_plugin_from_mcp_server(
    plugin_name: str,
    description: str | None = None,
    server_config: MCPServerConfig | None = None,
    **kwargs: Any,
) -> tuple[KernelPlugin, MCPServerConfig]:
    """Creates a KernelPlugin from a MCP server config.

    Args:
        plugin_name: The name of the plugin.
        description: The description of the plugin.
        server_config: The MCP client to use for communication,
            should be a MCPStdioServerConfig or MCPSseServerConfig.
            If not supplied, it will be created from the kwargs.
        kwargs: Any extra arguments to pass to the plugin creation.

    Returns:
        KernelPlugin: The created plugin, this should then be passed to the kernel or a agent.
        MCPServerConfig: The server config used to create the plugin.

    """
    if server_config is None:
        if "url" in kwargs:
            try:
                server_config = MCPSseServerConfig(**kwargs)
            except Exception as e:
                raise KernelPluginInvalidConfigurationError(
                    f"Failed to create MCPSseServerConfig with args: {kwargs}"
                ) from e
        elif "command" in kwargs:
            try:
                server_config = MCPStdioServerConfig(**kwargs)
            except Exception as e:
                raise KernelPluginInvalidConfigurationError(
                    f"Failed to create MCPStdioServerConfig with args: {kwargs}"
                ) from e
        if server_config is None:
            raise KernelPluginInvalidConfigurationError(
                "Failed to create MCP server configuration, please provide a valid server_config or kwargs."
            )
    async with server_config.get_session() as session:
        try:
            tool_list = await session.list_tools()
        except Exception:
            tool_list = None
        tools = [
            KernelFunctionFromMethod(
                method=kernel_function(name=tool.name, description=tool.description)(
                    partial(server_config.call_tool, tool.name)
                ),
                parameters=get_parameters_from_mcp_tool(tool),
            )
            for tool in (tool_list.tools if tool_list else [])
        ]
        try:
            prompt_list = await session.list_prompts()
        except Exception:
            prompt_list = None
        prompts = [
            KernelFunctionFromMethod(
                method=kernel_function(name=prompt.name, description=prompt.description)(
                    partial(server_config.get_prompt, prompt.name)
                ),
                parameters=get_parameter_from_mcp_prompt(prompt),
            )
            for prompt in (prompt_list.prompts if prompt_list else [])
        ]
        return (KernelPlugin(name=plugin_name, description=description, functions=tools + prompts), server_config)


@asynccontextmanager
async def mcp_server_as_plugin(
    plugin_name: str,
    description: str | None = None,
    server_config: MCPServerConfig | None = None,
    **kwargs: Any,
) -> AsyncGenerator[KernelPlugin, None]:
    """Creates a KernelPlugin from a MCP server config.

    Args:
        plugin_name: The name of the plugin.
        description: The description of the plugin.
        server_config: The MCP client to use for communication,
            should be a MCPStdioServerConfig or MCPSseServerConfig.
            If not supplied, it will be created from the kwargs.
        kwargs: Any extra arguments to pass to the plugin creation.

    Yields:
        KernelPlugin: The created plugin, this should then be passed to the kernel or a agent.

    """
    server = None
    try:
        plugin, server = await create_plugin_from_mcp_server(
            plugin_name=plugin_name,
            description=description,
            server_config=server_config,
            **kwargs,
        )
        yield plugin
    finally:
        # Close the session if it was created in this context
        if server and server.session:
            await server.session.__aexit__()
