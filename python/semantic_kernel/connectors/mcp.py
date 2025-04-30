# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import logging
import sys
from abc import abstractmethod
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack, _AsyncGeneratorContextManager, suppress
from functools import partial
from typing import TYPE_CHECKING, Any

from mcp import types
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.websocket import websocket_client
from mcp.server.lowlevel import Server
from mcp.shared.context import RequestContext
from mcp.shared.exceptions import McpError
from mcp.shared.session import RequestResponder

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import FunctionExecutionException, KernelPluginInvalidConfigurationError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_types import OneOrMany, OptionalOneOrMany
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

if TYPE_CHECKING:
    from mcp.server.lowlevel.server import LifespanResultT


logger = logging.getLogger(__name__)

# region: Helpers

LOG_LEVEL_MAPPING: dict[types.LoggingLevel, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "notice": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
    "alert": logging.CRITICAL,
    "emergency": logging.CRITICAL,
}


@experimental
def _mcp_prompt_message_to_kernel_content(
    mcp_type: types.PromptMessage | types.SamplingMessage,
) -> ChatMessageContent:
    """Convert a MCP container type to a Semantic Kernel type."""
    return ChatMessageContent(
        role=AuthorRole(mcp_type.role),
        items=[_mcp_content_types_to_kernel_content(mcp_type.content)],
        inner_content=mcp_type,
    )


@experimental
def _mcp_call_tool_result_to_kernel_contents(
    mcp_type: types.CallToolResult,
) -> list[TextContent | ImageContent | BinaryContent]:
    """Convert a MCP container type to a Semantic Kernel type."""
    return [_mcp_content_types_to_kernel_content(item) for item in mcp_type.content]


@experimental
def _mcp_content_types_to_kernel_content(
    mcp_type: types.ImageContent | types.TextContent | types.EmbeddedResource,
) -> TextContent | ImageContent | BinaryContent:
    """Convert a MCP type to a Semantic Kernel type."""
    if isinstance(mcp_type, types.TextContent):
        return TextContent(text=mcp_type.text, inner_content=mcp_type)
    if isinstance(mcp_type, types.ImageContent):
        return ImageContent(data=mcp_type.data, mime_type=mcp_type.mimeType, inner_content=mcp_type)
    # subtypes of EmbeddedResource
    if isinstance(mcp_type.resource, types.TextResourceContents):
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
def _kernel_content_to_mcp_content_types(
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
                    blob=content.data_string, mimeType=content.mime_type, uri=content.uri or "sk://binary"
                ),
            )
        ]
    if isinstance(content, ChatMessageContent):
        messages: list[types.TextContent | types.ImageContent | types.EmbeddedResource] = []
        for item in content.items:
            if isinstance(item, (TextContent, ImageContent, BinaryContent)):
                messages.extend(_kernel_content_to_mcp_content_types(item))
            else:
                logger.debug("Unsupported content type: %s", type(item))
        return messages

    raise FunctionExecutionException(f"Unsupported content type: {type(content)}")


@experimental
def _get_parameter_dict_from_mcp_prompt(prompt: types.Prompt) -> list[dict[str, Any]]:
    """Creates a MCPFunction instance from a prompt."""
    # Check if 'properties' is missing or not a dictionary
    if not prompt.arguments:
        return []
    return [
        {
            "name": prompt_argument.name,
            "description": prompt_argument.description,
            "is_required": True,
            "type_object": str,
        }
        for prompt_argument in prompt.arguments
    ]


@experimental
def _get_parameter_dicts_from_mcp_tool(tool: types.Tool) -> list[dict[str, Any]]:
    """Creates an MCPFunction instance from a tool."""
    properties = tool.inputSchema.get("properties", None)
    required = tool.inputSchema.get("required", [])
    # Check if 'properties' is missing or not a dictionary
    if not properties:
        return []
    params = []
    for prop_name, prop_details in properties.items():
        prop_details = json.loads(prop_details) if isinstance(prop_details, str) else prop_details

        params.append({
            "name": prop_name,
            "is_required": prop_name in required,
            "type": prop_details.get("type"),
            "default_value": prop_details.get("default", None),
            "schema_data": prop_details,
        })
    return params


# region: MCP Plugin


@experimental
class MCPPluginBase:
    """MCP Plugin Base."""

    def __init__(
        self,
        name: str,
        description: str | None = None,
        session: ClientSession | None = None,
        kernel: Kernel | None = None,
    ) -> None:
        """Initialize the MCP Plugin Base."""
        self.name = name
        self.description = description
        self._exit_stack = AsyncExitStack()
        self.session = session
        self.kernel = kernel or None

    async def connect(self) -> None:
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
                session = await self._exit_stack.enter_async_context(
                    ClientSession(
                        read_stream=transport[0],
                        write_stream=transport[1],
                        message_handler=self.message_handler,
                        logging_callback=self.logging_callback,
                        sampling_callback=self.sampling_callback,
                    )
                )
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
        logger.debug("Connected to MCP server: %s", self.session)
        with suppress(Exception):
            logger.debug("Resources: %s", await self.session.list_resources())
        with suppress(Exception):
            logger.debug("Resource templates: %s", await self.session.list_resource_templates())
        await self.load_tools()
        await self.load_prompts()

        if logger.level != logging.NOTSET:
            try:
                await self.session.set_logging_level(
                    next(level for level, value in LOG_LEVEL_MAPPING.items() if value == logger.level)
                )
            except Exception:
                logger.warning("Failed to set log level to %s", logger.level)

    async def sampling_callback(
        self, context: RequestContext[ClientSession, Any], params: types.CreateMessageRequestParams
    ) -> types.CreateMessageResult | types.ErrorData:
        """Callback function for sampling.

        This function is called when the MCP server needs to get a message completed.

        This is a simple version of this function, it can be overridden to allow more complex sampling.
        It get's added to the session at initialization time, so overriding it is the best way to do this.
        """
        if not self.kernel or not self.kernel.services:
            return types.ErrorData(
                code=types.INTERNAL_ERROR,
                message="No services in Kernel. Please set a kernel with one or more services.",
            )
        logger.debug("Sampling callback called with params: %s", params)
        if params.modelPreferences is not None and params.modelPreferences.hints:
            # TODO (eavanvalkenburg): deal with other parts of the modelPreferences concept
            names = [hint.name for hint in params.modelPreferences.hints]
        else:
            names = ["default"]

        for name in names:
            service = self.kernel.get_service(name, ChatCompletionClientBase)
            break
        if not service:
            service = self.kernel.get_service("default", ChatCompletionClientBase)
            if not service:
                return types.ErrorData(
                    code=types.INTERNAL_ERROR,
                    message="No Chat completion service found.",
                )
        completion_settings = service.get_prompt_execution_settings_class()()
        if "temperature" in completion_settings.__class__.model_fields:
            completion_settings.temperature = params.temperature  # type: ignore

        if "max_completion_tokens" in completion_settings.__class__.model_fields:
            completion_settings.max_completion_tokens = params.maxTokens  # type: ignore
        elif "max_tokens" in completion_settings.__class__.model_fields:
            completion_settings.max_tokens = params.maxTokens  # type: ignore
        elif "max_output_tokens" in completion_settings.__class__.model_fields:
            completion_settings.max_output_tokens = params.maxTokens  # type: ignore
        chat_history = ChatHistory(system_message=params.systemPrompt)
        for msg in params.messages:
            chat_history.add_message(_mcp_prompt_message_to_kernel_content(msg))
        try:
            result = await service.get_chat_message_content(
                chat_history,
                completion_settings,
            )
        except Exception as ex:
            return types.ErrorData(
                code=types.INTERNAL_ERROR,
                message=f"Failed to get chat message content: {ex}",
            )
        if not result:
            return types.ErrorData(
                code=types.INTERNAL_ERROR,
                message="Failed to get chat message content.",
            )
        mcp_contents = _kernel_content_to_mcp_content_types(result)
        # grab the first content that is of type TextContent or ImageContent
        mcp_content = next(
            (content for content in mcp_contents if isinstance(content, (types.TextContent, types.ImageContent))),
            None,
        )
        if not mcp_content:
            return types.ErrorData(
                code=types.INTERNAL_ERROR,
                message="Failed to get right content types from the response.",
            )
        return types.CreateMessageResult(
            role="assistant",
            content=mcp_content,
            model=service.ai_model_id,
        )

    async def logging_callback(self, params: types.LoggingMessageNotificationParams) -> None:
        """Callback function for logging.

        This function is called when the MCP Server sends a log message.
        By default it will log the message to the logger with the level set in the params.

        Please subclass the MCP*Plugin and override this function if you want to adapt the behavior.
        """
        logger.log(LOG_LEVEL_MAPPING[params.level], params.data)

    async def message_handler(
        self,
        message: RequestResponder[types.ServerRequest, types.ClientResult] | types.ServerNotification | Exception,
    ) -> None:
        """Handle messages from the MCP server.

        By default this function will handle exceptions on the server, by logging those.

        And it will trigger a reload of the tools and prompts when the list changed notification is received.

        If you want to extend this behavior you can subclass the MCPPlugin and override this function,
        if you want to keep the default behavior, make sure to call `super().message_handler(message)`.
        """
        if isinstance(message, Exception):
            logger.error("Error from MCP server: %s", message)
            return
        if isinstance(message, types.ServerNotification):
            match message.root.method:
                case "notifications/tools/list_changed":
                    await self.load_tools()
                case "notifications/prompts/list_changed":
                    await self.load_prompts()

    async def load_prompts(self):
        """Load prompts from the MCP server."""
        try:
            prompt_list = await self.session.list_prompts()
        except Exception:
            prompt_list = None
        for prompt in prompt_list.prompts if prompt_list else []:
            func = kernel_function(name=prompt.name, description=prompt.description)(
                partial(self.get_prompt, prompt.name)
            )
            func.__kernel_function_parameters__ = _get_parameter_dict_from_mcp_prompt(prompt)
            setattr(self, prompt.name, func)

    async def load_tools(self):
        """Load tools from the MCP server."""
        try:
            tool_list = await self.session.list_tools()
        except Exception:
            tool_list = None
            # Create methods with the kernel_function decorator for each tool
        for tool in tool_list.tools if tool_list else []:
            func = kernel_function(name=tool.name, description=tool.description)(partial(self.call_tool, tool.name))
            func.__kernel_function_parameters__ = _get_parameter_dicts_from_mcp_tool(tool)
            setattr(self, tool.name, func)

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
            return _mcp_call_tool_result_to_kernel_contents(await self.session.call_tool(tool_name, arguments=kwargs))
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
            return [_mcp_prompt_message_to_kernel_content(message) for message in prompt_result.messages]
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

    def added_to_kernel(self, kernel: Kernel) -> None:
        """Add the plugin to the kernel."""
        self.kernel = kernel


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
        kernel: Kernel | None = None,
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
            kernel: The kernel instance with one or more Chat Completion clients.
            kwargs: Any extra arguments to pass to the stdio client.

        """
        super().__init__(name, description, session, kernel)
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
        kernel: Kernel | None = None,
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
            kernel: The kernel instance with one or more Chat Completion clients.
            kwargs: Any extra arguments to pass to the sse client.

        """
        super().__init__(name=name, description=description, session=session, kernel=kernel)
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
        kernel: Kernel | None = None,
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
            kernel: The kernel instance with one or more Chat Completion clients.
            kwargs: Any extra arguments to pass to the websocket client.

        """
        super().__init__(name=name, description=description, session=session, kernel=kernel)
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


@experimental
def create_mcp_server_from_functions(
    functions: OneOrMany[KernelFunction | KernelPlugin | object],
    *,
    prompts: list[PromptTemplateBase] | None = None,
    server_name: str = "SK",
    version: str | None = None,
    instructions: str | None = None,
    lifespan: Callable[[Server["LifespanResultT"]], AbstractAsyncContextManager["LifespanResultT"]] | None = None,
    plugin_name: str = "mcp",
    **kwargs: Any,
) -> Server["LifespanResultT"]:
    """Create an MCP server from a function(s) or plugin(s).

    This function automatically creates a MCP server from single or multiple functions or plugins,
    all functions are added under the plugin_name that can be set by using the `plugin_name` argument.
    It further uses the provided arguments to
    configure the server and expose functions as tools, see the mcp documentation for more details.

    Args:
        functions: The function(s) or plugin(s) instance to use.
            This can be a mix of functions, plugins or agents.
            Or any object that can be parsed to a plugin.
        prompts: The list of prompts to expose as prompts.
        server_name: The name of the server.
        version: The version of the server.
        instructions: The instructions to use for the server.
        lifespan: The lifespan of the server.
        plugin_name: The name of the plugin to use.
        kwargs: Any extra arguments to pass to the server creation.

    Returns:
        The MCP server instance, it is a instance of
        mcp.server.lowlevel.Server

    """
    kernel = Kernel()
    if not isinstance(functions, list):
        functions = [functions]
    for func in functions:
        if isinstance(func, KernelFunction):
            kernel.add_function(plugin_name, func)
        else:
            try:
                kernel.add_plugin(func, plugin_name)
            except ValueError as ex:
                logger.warning(
                    "Failed to add plugin %s to kernel: %s",
                    func.__class__.__name__,
                    ex,
                )
    return create_mcp_server_from_kernel(
        kernel=kernel,
        prompts=prompts,
        server_name=server_name,
        version=version,
        instructions=instructions,
        lifespan=lifespan,
        **kwargs,
    )


@experimental
def create_mcp_server_from_kernel(
    kernel: Kernel,
    prompts: list[PromptTemplateBase] | None = None,
    *,
    server_name: str = "SK",
    version: str | None = None,
    instructions: str | None = None,
    lifespan: Callable[[Server["LifespanResultT"]], AbstractAsyncContextManager["LifespanResultT"]] | None = None,
    excluded_functions: OptionalOneOrMany[str] = None,
    **kwargs: Any,
) -> Server["LifespanResultT"]:
    """Create an MCP server from a kernel instance.

    This function automatically creates a MCP server from a kernel instance, it uses the provided arguments to
    configure the server and expose functions as tools and prompts, see the mcp documentation for more details.

    By default, all functions are exposed as Tools, you can control this by using use the `excluded_functions` argument.
    These need to be set to the function name, without the plugin_name.

    Args:
        kernel: The kernel instance to use.
        prompts: The list of prompts to expose as prompts.
        server_name: The name of the server.
        version: The version of the server.
        instructions: The instructions to use for the server.
        lifespan: The lifespan of the server.
        excluded_functions: The list of function names to exclude from the server.
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

    functions_to_expose = [
        func for func in kernel.get_full_list_of_function_metadata() if func.name not in (excluded_functions or [])
    ]

    if len(functions_to_expose) > 0:

        @server.list_tools()
        async def _list_tools() -> list[types.Tool]:
            """List all tools in the kernel."""
            tools = [
                types.Tool(
                    name=func.name,
                    description=func.description,
                    inputSchema={
                        "type": "object",
                        "properties": {
                            param.name: param.schema_data
                            for param in func.parameters
                            if param.name and param.schema_data and param.include_in_function_choices
                        },
                        "required": [
                            param.name
                            for param in func.parameters
                            if param.name and param.is_required and param.include_in_function_choices
                        ],
                    },
                )
                for func in functions_to_expose
            ]
            await _log(level="debug", data=f"List of tools: {tools}")
            await asyncio.sleep(0.0)
            return tools

        @server.call_tool()
        async def _call_tool(*args: Any) -> Sequence[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """Call a tool in the kernel."""
            await _log(level="debug", data=f"Calling tool with args: {args}")
            function_name, arguments = args[0], args[1]
            result = await _call_kernel_function(function_name, arguments)
            if result:
                value = result.value
                messages: list[types.TextContent | types.ImageContent | types.EmbeddedResource] = []
                if isinstance(value, list):
                    for item in value:
                        if isinstance(value, (TextContent, ImageContent, BinaryContent, ChatMessageContent)):
                            messages.extend(_kernel_content_to_mcp_content_types(item))
                        else:
                            messages.append(
                                types.TextContent(type="text", text=str(item)),
                            )
                else:
                    if isinstance(value, (TextContent, ImageContent, BinaryContent, ChatMessageContent)):
                        messages.extend(_kernel_content_to_mcp_content_types(value))
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

    if prompts:

        @server.list_prompts()
        async def _list_prompts() -> list[types.Prompt]:
            """List all prompts in the kernel."""
            mcp_prompts = []
            for prompt in prompts:
                mcp_prompts.append(
                    types.Prompt(
                        name=prompt.prompt_template_config.name,
                        description=prompt.prompt_template_config.description,
                        arguments=[
                            types.PromptArgument(
                                name=var.name,
                                description=var.description,
                                required=var.is_required,
                            )
                            for var in prompt.prompt_template_config.input_variables
                        ],
                    )
                )
            await _log(level="debug", data=f"List of prompts: {mcp_prompts}")
            return mcp_prompts

        @server.get_prompt()
        async def _get_prompt(name: str, arguments: dict[str, Any] | None) -> types.GetPromptResult:
            """Get a prompt by name."""
            prompt = next((p for p in prompts if p.prompt_template_config.name == name), None)
            if prompt is None:
                return types.GetPromptResult(description="Prompt not found", messages=[])

            # Call the prompt
            rendered_prompt = await prompt.render(
                kernel,
                KernelArguments(**arguments) if arguments is not None else KernelArguments(),
            )
            # since the return type of a get_prompts is a list of messages,
            # we need to convert the rendered prompt to a list of messages
            # by using the ChatHistory class
            chat_history = ChatHistory.from_rendered_prompt(rendered_prompt)
            messages = []
            for message in chat_history.messages:
                messages.append(
                    types.PromptMessage(
                        role=message.role.value
                        if message.role in (AuthorRole.ASSISTANT, AuthorRole.USER)
                        else "assistant",
                        content=_kernel_content_to_mcp_content_types(message)[0],
                    )
                )
            return types.GetPromptResult(messages=messages)

    async def _log(level: types.LoggingLevel, data: Any) -> None:
        """Log a message to the server and logger."""
        # Log to the local logger
        logger.log(LOG_LEVEL_MAPPING[level], data)
        if server and server.request_context and server.request_context.session:
            try:
                await server.request_context.session.send_log_message(level=level, data=data)
            except Exception as e:
                logger.error("Failed to send log message to server: %s", e)

    @server.set_logging_level()
    async def _set_logging_level(level: types.LoggingLevel) -> None:
        """Set the logging level for the server."""
        logger.setLevel(LOG_LEVEL_MAPPING[level])
        # emit this log with the new minimum level
        await _log(level=level, data=f"Log level set to {level}")

    async def _call_kernel_function(function_name: str, arguments: Any) -> FunctionResult | None:
        function = kernel.get_function(plugin_name=None, function_name=function_name)
        arguments["server"] = server
        print("arguments", arguments)
        return await function.invoke(kernel=kernel, **arguments)

    return server
