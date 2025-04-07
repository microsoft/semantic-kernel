# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from abc import abstractmethod
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack, _AsyncGeneratorContextManager
from functools import partial
from typing import TYPE_CHECKING, Any

from mcp import McpError, types
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.websocket import websocket_client
from mcp.server.lowlevel.server import Server
from mcp.types import CallToolResult, EmbeddedResource, Prompt, PromptMessage, TextResourceContents, Tool
from mcp.types import (
    ImageContent as MCPImageContent,
)
from mcp.types import (
    TextContent as MCPTextContent,
)

from semantic_kernel import Kernel
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_types import OptionalOneOrMany
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

if TYPE_CHECKING:
    from mcp.server.lowlevel.server import LifespanResultT


logger = logging.getLogger(__name__)

# region: Helpers


@experimental
def _mcp_prompt_message_to_semantic_kernel_type(
    mcp_type: PromptMessage,
) -> ChatMessageContent:
    """Convert a MCP container type to a Semantic Kernel type."""
    return ChatMessageContent(
        role=AuthorRole(mcp_type.role),
        items=[_mcp_type_to_semantic_kernel_type(mcp_type.content)],
        inner_content=mcp_type,
    )


@experimental
def _mcp_call_tool_result_to_semantic_kernel_type(
    mcp_type: CallToolResult,
) -> list[TextContent | ImageContent | BinaryContent]:
    """Convert a MCP container type to a Semantic Kernel type."""
    return [_mcp_type_to_semantic_kernel_type(item) for item in mcp_type.content]


@experimental
def _mcp_type_to_semantic_kernel_type(
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


@experimental
def get_parameter_from_mcp_prompt(prompt: Prompt) -> list[dict[str, Any]]:
    """Creates a MCPFunction instance from a prompt."""
    # Check if 'properties' is missing or not a dictionary
    if not prompt.arguments:
        return []
    return [
        dict(
            name=prompt_argument.name,
            description=prompt_argument.description,
            is_required=True,
            type_object=str,
        )
        for prompt_argument in prompt.arguments
    ]


@experimental
def get_parameters_from_mcp_tool(tool: Tool) -> list[dict[str, Any]]:
    """Creates an MCPFunction instance from a tool."""
    properties = tool.inputSchema.get("properties", None)
    required = tool.inputSchema.get("required", [])
    # Check if 'properties' is missing or not a dictionary
    if not properties:
        return []
    return [
        dict(
            name=prop_name,
            is_required=prop_name in required,
            type=prop_details.get("type"),
            default_value=prop_details.get("default", None),
            schema_data=prop_details,
        )
        for prop_name, prop_details in properties.items()
    ]


# region: MCP Plugin


@experimental
class MCPPluginBase:
    """MCP Plugin Base."""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        session: ClientSession | None = None,
    ) -> None:
        """Initialize the MCP Plugin Base."""
        self.name = name
        self.description = description
        self._tools_parsed = False
        self._prompts_parsed = False
        self._exit_stack = AsyncExitStack()
        self.session = session

    async def connect(self, force_reload: bool = False) -> None:
        """Connect to the MCP server."""
        if not self.session:
            try:
                transport = await self._exit_stack.enter_async_context(self.get_mcp_client())
            except Exception as ex:
                await self._exit_stack.aclose()
                raise KernelPluginInvalidConfigurationError(
                    "Failed to connect to the MCP server. Please check your configuration."
                ) from ex
            try:
                session = await self._exit_stack.enter_async_context(ClientSession(*transport))
            except Exception as ex:
                await self._exit_stack.aclose()
                raise KernelPluginInvalidConfigurationError(
                    "Failed to create a session. Please check your configuration."
                ) from ex
            await session.initialize()
            self.session = session
        elif self.session._request_id == 0:
            # If the session is not initialized, we need to reinitialize it
            await self.session.initialize()
        if not self._tools_parsed or force_reload:
            try:
                tool_list = await self.session.list_tools()
            except Exception:
                tool_list = None
            # Create methods with the kernel_function decorator for each tool
            for tool in tool_list.tools if tool_list else []:
                func = kernel_function(name=tool.name, description=tool.description)(partial(self.call_tool, tool.name))
                func.__kernel_function_parameters__ = get_parameters_from_mcp_tool(tool)
                setattr(self, tool.name, func)

            self._tools_parsed = True  # Mark tools as parsed

        if not self._prompts_parsed or force_reload:
            try:
                prompt_list = await self.session.list_prompts()
            except Exception:
                prompt_list = None
            for prompt in prompt_list.prompts if prompt_list else []:
                func = kernel_function(name=prompt.name, description=prompt.description)(
                    partial(self.get_prompt, prompt.name)
                )
                func.__kernel_function_parameters__ = get_parameter_from_mcp_prompt(prompt)
                setattr(self, prompt.name, func)

            self._prompts_parsed = True

    async def close(self) -> None:
        """Disconnect from the MCP server."""
        await self._exit_stack.aclose()
        self.session = None

    @abstractmethod
    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP client."""
        pass

    async def call_tool(self, tool_name: str, **kwargs: Any) -> list[TextContent | ImageContent | BinaryContent]:
        """Call a tool with the given arguments."""
        if not self.session:
            raise KernelPluginInvalidConfigurationError(
                "MCP server not connected, please call connect() before using this method."
            )
        try:
            return _mcp_call_tool_result_to_semantic_kernel_type(
                await self.session.call_tool(tool_name, arguments=kwargs)
            )
        except McpError:
            raise
        except Exception as ex:
            raise FunctionExecutionException(f"Failed to call tool '{tool_name}'.") from ex

    async def get_prompt(self, prompt_name: str, **kwargs: Any) -> list[ChatMessageContent]:
        """Call a prompt with the given arguments."""
        if not self.session:
            raise KernelPluginInvalidConfigurationError(
                "MCP server not connected, please call connect() before using this method."
            )
        try:
            prompt_result = await self.session.get_prompt(prompt_name, arguments=kwargs)
            return [_mcp_prompt_message_to_semantic_kernel_type(message) for message in prompt_result.messages]
        except McpError:
            raise
        except Exception as ex:
            raise FunctionExecutionException(f"Failed to call prompt '{prompt_name}'.") from ex

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        try:
            await self.connect()
            return self
        except KernelPluginInvalidConfigurationError:
            raise
        except Exception as ex:
            await self._exit_stack.aclose()
            raise FunctionExecutionException("Failed to enter context manager.") from ex

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Any
    ) -> None:
        """Exit the context manager."""
        await self.close()


# region: MCP Plugin Implementations


class MCPStdioPlugin(MCPPluginBase):
    """MCP stdio server configuration."""

    def __init__(
        self,
        name: str,
        command: str,
        session: ClientSession | None = None,
        description: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the MCP stdio plugin.

        The arguments are used to create a StdioServerParameters object.
        Which is then used to create a stdio client.
        see mcp.client.stdio.stdio_client and mcp.client.stdio.stdio_server_parameters
        for more details.

        Args:
            name: The name of the plugin.
            command: The command to run the MCP server.
            session: The session to use for the MCP connection.
            description: The description of the plugin.
            args: The arguments to pass to the command.
            env: The environment variables to set for the command.
            encoding: The encoding to use for the command output.
            kwargs: Any extra arguments to pass to the stdio client.

        """
        super().__init__(name, description, session)
        self.command = command
        self.args = args or []
        self.env = env
        self.encoding = encoding
        self._client_kwargs = kwargs

    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP stdio client."""
        args = {
            "command": self.command,
            "args": self.args,
            "env": self.env,
        }
        if self.encoding:
            args["encoding"] = self.encoding
        if self._client_kwargs:
            args.update(self._client_kwargs)
        return stdio_client(server=StdioServerParameters(**args))


class MCPSsePlugin(MCPPluginBase):
    """MCP sse server configuration."""

    def __init__(
        self,
        name: str,
        url: str,
        session: ClientSession | None = None,
        description: str | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
        sse_read_timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the MCP sse plugin.

                The arguments are used to create a sse client.
        see mcp.client.sse.sse_client for more details.

        Any extra arguments passed to the constructor will be passed to the
        sse client constructor.

        Args:
            name: The name of the plugin.
            url: The URL of the MCP server.
            session: The session to use for the MCP connection.
            description: The description of the plugin.
            headers: The headers to send with the request.
            timeout: The timeout for the request.
            sse_read_timeout: The timeout for reading from the SSE stream.
            kwargs: Any extra arguments to pass to the sse client.

        """
        super().__init__(name, description, session)
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout
        self.sse_read_timeout = sse_read_timeout
        self._client_kwargs = kwargs

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
        if self._client_kwargs:
            args.update(self._client_kwargs)
        return sse_client(**args)


class MCPWebsocketPlugin(MCPPluginBase):
    """MCP websocket server configuration."""

    def __init__(
        self,
        name: str,
        url: str,
        session: ClientSession | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the MCP websocket plugin.

                The arguments are used to create a websocket client.
        see mcp.client.websocket.websocket_client for more details.

        Any extra arguments passed to the constructor will be passed to the
        websocket client constructor.

        Args:
            name: The name of the plugin.
            url: The URL of the MCP server.
            session: The session to use for the MCP connection.
            description: The description of the plugin.
            kwargs: Any extra arguments to pass to the websocket client.

        """
        super().__init__(name, description, session)
        self.url = url
        self._client_kwargs = kwargs

    def get_mcp_client(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Get an MCP websocket client."""
        args: dict[str, Any] = {
            "url": self.url,
        }
        if self._client_kwargs:
            args.update(self._client_kwargs)
        return websocket_client(**args)


# region: Kernel as MCP Server


def _kernel_content_to_mcp_type(
    content: TextContent | ImageContent | BinaryContent | ChatMessageContent,
) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Convert a kernel content type to a MCP type."""
    if isinstance(content, TextContent):
        return [types.TextContent(type="text", text=content.text)]
    if isinstance(content, ImageContent):
        return [types.ImageContent(type="image", data=content.data_string, mimeType=content.mime_type)]
    if isinstance(content, BinaryContent):
        return [
            types.EmbeddedResource(
                type="resource",
                resource=types.BlobResourceContents(
                    blob=content.data_string, mimeType=content.mime_type, uri=content.uri or "kernel:///binary"
                ),
            )
        ]
    if isinstance(content, ChatMessageContent):
        messages: list[types.TextContent | types.ImageContent | types.EmbeddedResource] = []
        for item in content.items:
            if isinstance(item, (TextContent, ImageContent, BinaryContent)):
                messages.extend(_kernel_content_to_mcp_type(item))
        return messages

    raise FunctionExecutionException(f"Unsupported content type: {type(content)}")


def create_mcp_server_from_kernel(
    kernel: Kernel,
    *,
    server_name: str = "Semantic Kernel MCP Server",
    version: str | None = None,
    instructions: str | None = None,
    lifespan: Callable[[Server["LifespanResultT"]], AbstractAsyncContextManager["LifespanResultT"]] | None = None,
    excluded_functions: OptionalOneOrMany[str] = None,
    **kwargs: Any,
) -> Server["LifespanResultT"]:
    """Create an MCP server from a kernel instance.

    This function automatically creates a MCP server from a kernel instance, it uses the provided arguments to
    configure the server and expose functions as tools and prompts, see the mcp documentation for more details.

    By default, all functions are exposed as Tools, you can specify which functions,
    to do this you can use the `excluded_functions` argument.
    These need to be set to the fully qualified function name (i.e. `<plugin_name>-<function_name>`).

    Args:
        kernel: The kernel instance to use.
        server_name: The name of the server.
        version: The version of the server.
        instructions: The instructions to use for the server.
        lifespan: The lifespan of the server.
        excluded_functions: The list of fully qualified function names to exclude from the server.
            if None, no functions will be excluded.
        kwargs: Any extra arguments to pass to the server creation.

    Returns:
        The MCP server instance, it is a instance of
        mcp.server.lowlevel.Server

    """
    server_args: dict[str, Any] = {
        "name": server_name,
        "version": version,
        "instructions": instructions,
    }
    if lifespan:
        server_args["lifespan"] = lifespan
    if kwargs:
        server_args.update(kwargs)

    if excluded_functions is not None and not isinstance(excluded_functions, list):
        excluded_functions = [excluded_functions]  # type: ignore

    server: Server["LifespanResultT"] = Server(**server_args)  # type: ignore[call-arg]

    @server.list_tools()
    async def _list_tools() -> list[types.Tool]:
        """List all tools in the kernel."""
        functions_to_expose = [
            func
            for func in kernel.get_full_list_of_function_metadata()
            if func.fully_qualified_name not in (excluded_functions or [])
        ]
        tools = [
            types.Tool(
                name=func.fully_qualified_name,
                description=func.description,
                inputSchema={
                    "type": "object",
                    "properties": {
                        param.name: param.schema_data for param in func.parameters if param.name and param.schema_data
                    },
                    "required": [param.name for param in func.parameters if param.name and param.is_required],
                },
            )
            for func in functions_to_expose
        ]
        logger.debug(f"Tools: {tools}")
        await asyncio.sleep(0.0)
        return tools

    @server.call_tool()
    async def _call_tool(*args: Any) -> list[types.TextContent]:
        """Call a tool in the kernel."""
        logger.debug("Tool called with args: %s", args)
        function_name, arguments = args[0], args[1]
        result = await _call_kernel_function(function_name, arguments)
        if result:
            value = result.value
            messages = []
            if isinstance(value, list):
                for item in value:
                    if isinstance(value, KernelContent):
                        messages.extend(_kernel_content_to_mcp_type(item))
                    else:
                        messages.append(
                            types.TextContent(type="text", text=str(item)),
                        )
            else:
                if isinstance(value, KernelContent):
                    messages.extend(_kernel_content_to_mcp_type(value))
                else:
                    messages.append(
                        types.TextContent(type="text", text=str(value)),
                    )
            return messages
        raise McpError(
            error=types.ErrorData(
                code=types.INTERNAL_ERROR,
                message=f"Function {function_name} returned no result",
            ),
        )

    async def _call_kernel_function(function_name: str, arguments: Any) -> FunctionResult | None:
        function = kernel.get_function_from_fully_qualified_function_name(function_name)
        return await function.invoke(kernel=kernel, **arguments)

    return server
