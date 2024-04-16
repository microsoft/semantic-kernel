# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging
from copy import copy
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Literal, Type, TypeVar, Union

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.events import FunctionInvokedEventArgs, FunctionInvokingEventArgs
from semantic_kernel.exceptions import (
    KernelFunctionAlreadyExistsError,
    KernelFunctionNotFoundError,
    KernelInvokeException,
    KernelPluginNotFoundError,
    KernelServiceNotFoundError,
    ServiceInvalidTypeError,
    TemplateSyntaxError,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME, TEMPLATE_FORMAT_TYPES
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.reliability.pass_through_without_retry import PassThroughWithoutRetry
from semantic_kernel.reliability.retry_mechanism_base import RetryMechanismBase
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
    from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
    from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
    from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
        OpenAIFunctionExecutionParameters,
    )
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.functions.types import KERNEL_FUNCTION_TYPE

T = TypeVar("T")

ALL_SERVICE_TYPES = Union["TextCompletionClientBase", "ChatCompletionClientBase", "EmbeddingGeneratorBase"]

logger: logging.Logger = logging.getLogger(__name__)


class Kernel(KernelBaseModel):
    """
    The Kernel class is the main entry point for the Semantic Kernel. It provides the ability to run
    semantic/native functions, and manage plugins, memory, and AI services.

    Attributes:
        plugins (dict[str, KernelPlugin] | None): The plugins to be used by the kernel
        services (dict[str, AIServiceClientBase]): The services to be used by the kernel
        retry_mechanism (RetryMechanismBase): The retry mechanism to be used by the kernel
        function_invoking_handlers (dict): The function invoking handlers
        function_invoked_handlers (dict): The function invoked handlers
    """

    # region Init

    plugins: dict[str, KernelPlugin] = Field(default_factory=dict)
    services: dict[str, AIServiceClientBase] = Field(default_factory=dict)
    ai_service_selector: AIServiceSelector = Field(default_factory=AIServiceSelector)
    retry_mechanism: RetryMechanismBase = Field(default_factory=PassThroughWithoutRetry)
    function_invoking_handlers: dict[
        int, Callable[["Kernel", FunctionInvokingEventArgs], FunctionInvokingEventArgs]
    ] = Field(default_factory=dict)
    function_invoked_handlers: dict[int, Callable[["Kernel", FunctionInvokedEventArgs], FunctionInvokedEventArgs]] = (
        Field(default_factory=dict)
    )

    def __init__(
        self,
        plugins: KernelPlugin | dict[str, KernelPlugin] | list[KernelPlugin] | None = None,
        services: AIServiceClientBase | list[AIServiceClientBase] | dict[str, AIServiceClientBase] | None = None,
        ai_service_selector: AIServiceSelector | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new instance of the Kernel class.

        Args:
            plugins (KernelPlugin | dict[str, KernelPlugin] | list[KernelPlugin] | None):
                The plugins to be used by the kernel, will be rewritten to a dict with plugin name as key
            services (AIServiceClientBase | list[AIServiceClientBase] | dict[str, AIServiceClientBase] | None:
                The services to be used by the kernel, will be rewritten to a dict with service_id as key
            ai_service_selector (AIServiceSelector | None): The AI service selector to be used by the kernel,
                default is based on order of execution settings.
            **kwargs (Any): Additional fields to be passed to the Kernel model,
                these are limited to retry_mechanism and function_invoking_handlers
                and function_invoked_handlers, the best way to add function_invoking_handlers
                and function_invoked_handlers is to use the add_function_invoking_handler
                and add_function_invoked_handler methods.
        """
        args = {
            "services": services,
            "plugins": plugins,
            **kwargs,
        }
        if ai_service_selector:
            args["ai_service_selector"] = ai_service_selector
        super().__init__(**args)

    @field_validator("plugins", mode="before")
    @classmethod
    def rewrite_plugins(
        cls, plugins: KernelPlugin | list[KernelPlugin] | dict[str, KernelPlugin] | None = None
    ) -> dict[str, KernelPlugin]:
        """Rewrite plugins to a dictionary."""
        if not plugins:
            return {}
        if isinstance(plugins, KernelPlugin):
            return {plugins.name: plugins}
        if isinstance(plugins, list):
            return {p.name: p for p in plugins}
        return plugins

    @field_validator("services", mode="before")
    @classmethod
    def rewrite_services(
        cls,
        services: AIServiceClientBase | list[AIServiceClientBase] | dict[str, AIServiceClientBase] | None = None,
    ) -> dict[str, AIServiceClientBase]:
        """Rewrite services to a dictionary."""
        if not services:
            return {}
        if isinstance(services, AIServiceClientBase):
            return {services.service_id or "default": services}
        if isinstance(services, list):
            return {s.service_id or "default": s for s in services}
        return services

    # endregion
    # region Invoke Functions

    async def invoke_stream(
        self,
        function: "KernelFunction" | None = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        return_function_results: bool | None = False,
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingContentMixin"] | FunctionResult | list[FunctionResult], Any]:
        """Execute one or more stream functions.

        This will execute the functions in the order they are provided, if a list of functions is provided.
        When multiple functions are provided only the last one is streamed, the rest is executed as a pipeline.

        Arguments:
            functions (KernelFunction): The function or functions to execute,
            this value has precedence when supplying both this and using function_name and plugin_name,
            if this is none, function_name and plugin_name are used and cannot be None.
            arguments (KernelArguments): The arguments to pass to the function(s), optional
            function_name (str | None): The name of the function to execute
            plugin_name (str | None): The name of the plugin to execute
            return_function_results (bool | None): If True, the function results are returned in addition to
                the streaming content, otherwise only the streaming content is returned.
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Yields:
            StreamingContentMixin: The content of the stream of the last function provided.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        if not function:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError("No function(s) or function- and plugin-name provided")
            function = self.get_function(plugin_name, function_name)

        function_invoking_args = self.on_function_invoking(function.metadata, arguments)
        if function_invoking_args.is_cancel_requested:
            logger.info(
                f"Execution was cancelled on function invoking event of function: {function.fully_qualified_name}."
            )
            return
        if function_invoking_args.updated_arguments:
            logger.info(
                "Arguments updated by function_invoking_handler in function, "
                f"new arguments: {function_invoking_args.arguments}"
            )
            arguments = function_invoking_args.arguments
        if function_invoking_args.is_skip_requested:
            logger.info(
                f"Execution was skipped on function invoking event of function: {function.fully_qualified_name}."
            )
            return
        function_result: list[list["StreamingContentMixin"] | Any] = []

        async for stream_message in function.invoke_stream(self, arguments):
            if isinstance(stream_message, FunctionResult) and (
                exception := stream_message.metadata.get("exception", None)
            ):
                raise KernelInvokeException(
                    f"Error occurred while invoking function: '{function.fully_qualified_name}'"
                ) from exception
            function_result.append(stream_message)
            yield stream_message

        if return_function_results:
            output_function_result: list["StreamingContentMixin"] = []
            for result in function_result:
                for choice in result:
                    if not isinstance(choice, StreamingContentMixin):
                        continue
                    if len(output_function_result) <= choice.choice_index:
                        output_function_result.append(copy(choice))
                    else:
                        output_function_result[choice.choice_index] += choice
            yield FunctionResult(function=function.metadata, value=output_function_result)

    async def invoke(
        self,
        function: "KernelFunction" | None = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        **kwargs: Any,
    ) -> FunctionResult | None:
        """Execute one or more functions.

        When multiple functions are passed the FunctionResult of each is put into a list.

        Arguments:
            function (KernelFunction): The function or functions to execute,
            this value has precedence when supplying both this and using function_name and plugin_name,
            if this is none, function_name and plugin_name are used and cannot be None.
            arguments (KernelArguments): The arguments to pass to the function(s), optional
            function_name (str | None): The name of the function to execute
            plugin_name (str | None): The name of the plugin to execute
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Returns:
            FunctionResult | list[FunctionResult] | None: The result of the function(s)

        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        if not function:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError("No function or plugin name provided")
            function = self.get_function(plugin_name, function_name)
        function_invoking_args = self.on_function_invoking(function.metadata, arguments)
        if function_invoking_args.is_cancel_requested:
            logger.info(
                f"Execution was cancelled on function invoking event of function: {function.fully_qualified_name}."
            )
            return None
        if function_invoking_args.updated_arguments:
            logger.info(
                f"Arguments updated by function_invoking_handler, new arguments: {function_invoking_args.arguments}"
            )
            arguments = function_invoking_args.arguments
        function_result = None
        exception = None
        try:
            function_result = await function.invoke(self, arguments)
        except Exception as exc:
            logger.error(
                "Something went wrong in function invocation. During function invocation:"
                f" '{function.fully_qualified_name}'. Error description: '{str(exc)}'"
            )
            exception = exc

        # this allows a hook to alter the results before adding.
        function_invoked_args = self.on_function_invoked(function.metadata, arguments, function_result, exception)
        if function_invoked_args.exception:
            raise KernelInvokeException(
                f"Error occurred while invoking function: '{function.fully_qualified_name}'"
            ) from function_invoked_args.exception
        if function_invoked_args.is_cancel_requested:
            logger.info(
                f"Execution was cancelled on function invoked event of function: {function.fully_qualified_name}."
            )
            return (
                function_invoked_args.function_result
                if function_invoked_args.function_result
                else FunctionResult(function=function.metadata, value=None, metadata={})
            )
        if function_invoked_args.updated_arguments:
            logger.info(
                f"Arguments updated by function_invoked_handler in function {function.fully_qualified_name}"
                ", new arguments: {function_invoked_args.arguments}"
            )
            arguments = function_invoked_args.arguments
        if function_invoked_args.is_repeat_requested:
            logger.info(
                f"Execution was repeated on function invoked event of function: {function.fully_qualified_name}."
            )
            return await self.invoke(function=function, arguments=arguments)

        return (
            function_invoked_args.function_result
            if function_invoked_args.function_result
            else FunctionResult(function=function.metadata, value=None, metadata={})
        )

    async def invoke_prompt(
        self,
        function_name: str,
        plugin_name: str,
        prompt: str,
        arguments: KernelArguments | None = None,
        template_format: Literal[
            "semantic-kernel",
            "handlebars",
            "jinja2",
        ] = KERNEL_TEMPLATE_FORMAT_NAME,
        **kwargs: Any,
    ) -> FunctionResult | None:
        """
        Invoke a function from the provided prompt

        Args:
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            prompt (str): The prompt to use
            arguments (KernelArguments | None): The arguments to pass to the function(s), optional
            template_format (str | None): The format of the prompt template
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Returns:
            FunctionResult | list[FunctionResult] | None: The result of the function(s)
        """
        if not arguments:
            arguments = KernelArguments(**kwargs)
        if not prompt:
            raise TemplateSyntaxError("The prompt is either null or empty.")

        from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

        function = KernelFunctionFromPrompt(
            function_name=function_name,
            plugin_name=plugin_name,
            prompt=prompt,
            template_format=template_format,
        )
        return await self.invoke(function=function, arguments=arguments)

    # endregion
    # region Function Invoking/Invoked Events

    def on_function_invoked(
        self,
        kernel_function_metadata: KernelFunctionMetadata,
        arguments: KernelArguments,
        function_result: FunctionResult | None = None,
        exception: Exception | None = None,
    ) -> FunctionInvokedEventArgs:
        # TODO: include logic that uses function_result
        args = FunctionInvokedEventArgs(
            kernel_function_metadata=kernel_function_metadata,
            arguments=arguments,
            function_result=function_result,
            exception=exception or function_result.metadata.get("exception", None) if function_result else None,
        )
        if self.function_invoked_handlers:
            for handler in self.function_invoked_handlers.values():
                handler(self, args)
        return args

    def on_function_invoking(
        self, kernel_function_metadata: KernelFunctionMetadata, arguments: KernelArguments
    ) -> FunctionInvokingEventArgs:
        args = FunctionInvokingEventArgs(kernel_function_metadata=kernel_function_metadata, arguments=arguments)
        if self.function_invoking_handlers:
            for handler in self.function_invoking_handlers.values():
                handler(self, args)
        return args

    def add_function_invoking_handler(
        self, handler: Callable[["Kernel", FunctionInvokingEventArgs], FunctionInvokingEventArgs]
    ) -> None:
        self.function_invoking_handlers[id(handler)] = handler

    def add_function_invoked_handler(
        self, handler: Callable[["Kernel", FunctionInvokedEventArgs], FunctionInvokedEventArgs]
    ) -> None:
        self.function_invoked_handlers[id(handler)] = handler

    def remove_function_invoking_handler(self, handler: Callable) -> None:
        if id(handler) in self.function_invoking_handlers:
            del self.function_invoking_handlers[id(handler)]

    def remove_function_invoked_handler(self, handler: Callable) -> None:
        if id(handler) in self.function_invoked_handlers:
            del self.function_invoked_handlers[id(handler)]

    # endregion
    # region Plugins & Functions

    def add_plugin(
        self,
        plugin: KernelPlugin | Any | dict[str, Any] | None = None,
        plugin_name: str | None = None,
        parent_directory: str | None = None,
        description: str | None = None,
        class_init_arguments: dict[str, dict[str, Any]] | None = None,
    ) -> "KernelPlugin":
        """
        Adds a plugin to the kernel's collection of plugins. If a plugin is provided,
        it uses that instance instead of creating a new KernelPlugin.
        See KernelPlugin.from_directory for more details on how the directory is parsed.

        Args:
            plugin (KernelPlugin | Any | dict[str, Any]): The plugin to add.
                This can be a KernelPlugin, in which case it is added straightaway and other parameters are ignored,
                a custom class that contains methods with the kernel_function decorator
                or a dictionary of functions with the kernel_function decorator for one or
                several methods.
            plugin_name (str | None): The name of the plugin, used if the plugin is not a KernelPlugin,
                if the plugin is None and the parent_directory is set,
                KernelPlugin.from_directory is called with those parameters,
                see `KernelPlugin.from_directory` for details.
            parent_directory (str | None): The parent directory path where the plugin directory resides
            description (str | None): The description of the plugin, used if the plugin is not a KernelPlugin.
            class_init_arguments (dict[str, dict[str, Any]] | None): The class initialization arguments

        Returns:
            KernelPlugin: The plugin that was added.

        Raises:
            ValidationError: If a KernelPlugin needs to be created, but it is not valid.

        """
        if isinstance(plugin, KernelPlugin):
            self.plugins[plugin.name] = plugin
            return self.plugins[plugin.name]
        if not plugin_name:
            raise ValueError("plugin_name must be provided if a plugin is not supplied.")
        if plugin:
            self.plugins[plugin_name] = KernelPlugin.from_object(
                plugin_name=plugin_name, plugin_instance=plugin, description=description
            )
            return self.plugins[plugin_name]
        if plugin is None and parent_directory is not None:
            self.plugins[plugin_name] = KernelPlugin.from_directory(
                plugin_name=plugin_name,
                parent_directory=parent_directory,
                description=description,
                class_init_arguments=class_init_arguments,
            )
            return self.plugins[plugin_name]
        raise ValueError("plugin or parent_directory must be provided.")

    def add_plugins(self, plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object]) -> None:
        """
        Adds a list of plugins to the kernel's collection of plugins.

        Args:
            plugins (list[KernelPlugin] | dict[str, KernelPlugin]): The plugins to add to the kernel
        """
        if isinstance(plugins, list):
            for plugin in plugins:
                self.add_plugin(plugin)
            return
        for name, plugin in plugins.items():
            self.add_plugin(plugin, plugin_name=name)

    def add_function(
        self,
        plugin_name: str,
        function: KERNEL_FUNCTION_TYPE | None = None,
        function_name: str | None = None,
        description: str | None = None,
        prompt: str | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        prompt_execution_settings: (
            PromptExecutionSettings | list[PromptExecutionSettings] | dict[str, PromptExecutionSettings] | None
        ) = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: PromptTemplateBase | None = None,
        return_plugin: bool = False,
        **kwargs: Any,
    ) -> "KernelFunction | KernelPlugin":
        """
        Adds a function to the specified plugin.

        Args:
            plugin_name (str): The name of the plugin to add the function to
            function (KernelFunction | Callable[..., Any]): The function to add
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            description (str | None): The description of the function
            prompt (str | None): The prompt template.
            prompt_template_config (PromptTemplateConfig | None): The prompt template configuration
            prompt_execution_settings (PromptExecutionSettings  | list[PromptExecutionSettings]
                | dict[str, PromptExecutionSettings] | None):
                The execution settings, will be parsed into a dict.
            template_format (str | None): The format of the prompt template
            prompt_template (PromptTemplateBase | None): The prompt template
            return_plugin (bool): If True, the plugin is returned instead of the function
            kwargs (Any): Additional arguments

        Returns:
            KernelFunction | KernelPlugin: The function that was added, or the plugin if return_plugin is True

        """
        from semantic_kernel.functions.kernel_function import KernelFunction

        if function is None:
            if not function_name or (not prompt and not prompt_template_config and not prompt_template):
                raise ValueError(
                    "function_name and prompt, prompt_template_config or prompt_template must be provided if a function is not supplied."  # noqa: E501
                )
            if prompt_execution_settings is None and (
                prompt_template_config is None or prompt_template_config.execution_settings is None
            ):
                prompt_execution_settings = PromptExecutionSettings(extension_data=kwargs)

            function = KernelFunction.from_prompt(
                function_name=function_name,
                plugin_name=plugin_name,
                description=description,
                prompt=prompt,
                template_format=template_format,
                prompt_template=prompt_template,
                prompt_template_config=prompt_template_config,
                prompt_execution_settings=prompt_execution_settings,
            )
        elif not isinstance(function, KernelFunction):
            function = KernelFunction.from_method(plugin_name=plugin_name, method=function)
        if plugin_name not in self.plugins:
            plugin = KernelPlugin(name=plugin_name, functions=function)
            self.add_plugin(plugin)
            return plugin if return_plugin else plugin[function.name]
        self.plugins[plugin_name][function.name] = function
        return self.plugins[plugin_name] if return_plugin else self.plugins[plugin_name][function.name]

    def add_functions(
        self,
        plugin_name: str,
        functions: list[KERNEL_FUNCTION_TYPE] | dict[str, KERNEL_FUNCTION_TYPE],
    ) -> "KernelPlugin":
        """
        Adds a list of functions to the specified plugin.

        Args:
            plugin_name (str): The name of the plugin to add the functions to
            functions (list[KernelFunction] | dict[str, KernelFunction]): The functions to add

        Returns:
            KernelPlugin: The plugin that the functions were added to.

        """
        if plugin_name in self.plugins:
            self.plugins[plugin_name].update(functions)
            return self.plugins[plugin_name]
        return self.add_plugin(KernelPlugin(name=plugin_name, functions=functions))  # type: ignore

    def add_plugin_from_openapi(
        self,
        plugin_name: str,
        openapi_document_path: str,
        execution_settings: "OpenAPIFunctionExecutionParameters | None" = None,
        description: str | None = None,
    ) -> KernelPlugin:
        """Add a plugin from the Open AI manifest.

        Args:
            plugin_name (str): The name of the plugin
            plugin_url (str | None): The URL of the plugin
            plugin_str (str | None): The JSON string of the plugin
            execution_parameters (OpenAIFunctionExecutionParameters | None): The execution parameters

        Returns:
            KernelPlugin: The imported plugin

        Raises:
            PluginInitializationError: if the plugin URL or plugin JSON/YAML is not provided
        """
        return self.add_plugin(
            KernelPlugin.from_openapi(
                plugin_name=plugin_name,
                openapi_document_path=openapi_document_path,
                execution_settings=execution_settings,
                description=description,
            )
        )

    async def add_plugin_from_openai(
        self,
        plugin_name: str,
        plugin_url: str | None = None,
        plugin_str: str | None = None,
        execution_parameters: "OpenAIFunctionExecutionParameters | None" = None,
        description: str | None = None,
    ) -> KernelPlugin:
        """Add a plugin from an OpenAPI document.

        Args:
            plugin_name (str): The name of the plugin
            plugin_url (str | None): The URL of the plugin
            plugin_str (str | None): The JSON string of the plugin
            execution_parameters (OpenAIFunctionExecutionParameters | None): The execution parameters
            description (str | None): The description of the plugin

        Returns:
            KernelPlugin: The imported plugin

        Raises:
            PluginInitializationError: if the plugin URL or plugin JSON/YAML is not provided
        """
        return self.add_plugin(
            await KernelPlugin.from_openai(
                plugin_name=plugin_name,
                plugin_url=plugin_url,
                plugin_str=plugin_str,
                execution_parameters=execution_parameters,
                description=description,
            )
        )

    def get_plugin(self, plugin_name: str) -> "KernelPlugin":
        """Get a plugin by name.

        Args:
            plugin_name (str): The name of the plugin

        Returns:
            KernelPlugin: The plugin

        Raises:
            KernelPluginNotFoundError: If the plugin is not found

        """
        if plugin_name not in self.plugins:
            raise KernelPluginNotFoundError(f"Plugin '{plugin_name}' not found")
        return self.plugins[plugin_name]

    def get_function(self, plugin_name: str | None, function_name: str) -> "KernelFunction":
        """Get a function by plugin_name and function_name.

        Args:
            plugin_name (str | None): The name of the plugin
            function_name (str): The name of the function

        Returns:
            KernelFunction: The function

        Raises:
            KernelPluginNotFoundError: If the plugin is not found
            KernelFunctionNotFoundError: If the function is not found

        """
        if plugin_name is None:
            for plugin in self.plugins.values():
                if function_name in plugin:
                    return plugin[function_name]
            raise KernelFunctionNotFoundError(f"Function '{function_name}' not found in any plugin.")
        if plugin_name not in self.plugins:
            raise KernelPluginNotFoundError(f"Plugin '{plugin_name}' not found")
        if function_name not in self.plugins[plugin_name]:
            raise KernelFunctionNotFoundError(f"Function '{function_name}' not found in plugin '{plugin_name}'")
        return self.plugins[plugin_name][function_name]

    def get_function_from_fully_qualified_function_name(self, fully_qualified_function_name: str) -> "KernelFunction":
        """Get a function by its fully qualified name (<plugin_name>-<function_name>).

        Args:
            fully_qualified_function_name (str): The fully qualified name of the function,
                if there is no '-' in the name, it is assumed that it is only a function_name.

        Returns:
            KernelFunction: The function

        Raises:
            KernelPluginNotFoundError: If the plugin is not found
            KernelFunctionNotFoundError: If the function is not found

        """
        names = fully_qualified_function_name.split("-", maxsplit=1)
        if len(names) == 1:
            plugin_name = None
            function_name = names[0]
        else:
            plugin_name = names[0]
            function_name = names[1]
        return self.get_function(plugin_name, function_name)

    def get_list_of_function_metadata(
        self, include_prompt: bool = True, include_native: bool = True
    ) -> list[KernelFunctionMetadata]:
        """
        Get a list of the function metadata in the plugin collection

        Args:
            include_prompt (bool): Whether to include semantic functions in the list.
            include_native (bool): Whether to include native functions in the list.

        Returns:
            A list of KernelFunctionMetadata objects in the collection.
        """
        if not self.plugins:
            return []
        return [
            func.metadata
            for plugin in self.plugins.values()
            for func in plugin.functions.values()
            if (include_prompt and func.is_prompt) or (include_native and not func.is_prompt)
        ]

    # endregion
    # region Services

    def select_ai_service(
        self, function: "KernelFunction", arguments: KernelArguments
    ) -> tuple[ALL_SERVICE_TYPES, PromptExecutionSettings]:
        """Uses the AI service selector to select a service for the function."""
        return self.ai_service_selector.select_ai_service(self, function, arguments)

    def get_service(
        self,
        service_id: str | None = None,
        type: Type[ALL_SERVICE_TYPES] | None = None,
    ) -> "AIServiceClientBase":
        """Get a service by service_id and type.

        Type is optional and when not supplied, no checks are done.
        Type should be
            TextCompletionClientBase, ChatCompletionClientBase, EmbeddingGeneratorBase
            or a subclass of one.
            You can also check for multiple types in one go,
            by using TextCompletionClientBase | ChatCompletionClientBase.

        If type and service_id are both None, the first service is returned.

        Args:
            service_id (str | None): The service id,
                if None, the default service is returned or the first service is returned.
            type (Type[ALL_SERVICE_TYPES] | None): The type of the service, if None, no checks are done.

        Returns:
            ALL_SERVICE_TYPES: The service.

        Raises:
            ValueError: If no service is found that matches the type.

        """
        service: "AIServiceClientBase | None" = None
        if not service_id or service_id == "default":
            if not type:
                if default_service := self.services.get("default"):
                    return default_service
                return list(self.services.values())[0]
            if default_service := self.services.get("default"):
                if isinstance(default_service, type):
                    return default_service
            for service in self.services.values():
                if isinstance(service, type):
                    return service
            raise KernelServiceNotFoundError(f"No service found of type {type}")
        if not (service := self.services.get(service_id)):
            raise KernelServiceNotFoundError(f"Service with service_id '{service_id}' does not exist")
        if type and not isinstance(service, type):
            raise ServiceInvalidTypeError(f"Service with service_id '{service_id}' is not of type {type}")
        return service

    def get_services_by_type(self, type: Type[ALL_SERVICE_TYPES]) -> dict[str, "AIServiceClientBase"]:
        return {service.service_id: service for service in self.services.values() if isinstance(service, type)}

    def get_prompt_execution_settings_from_service_id(
        self, service_id: str, type: Type[ALL_SERVICE_TYPES] | None = None
    ) -> PromptExecutionSettings:
        """Get the specific request settings from the service, instantiated with the service_id and ai_model_id."""
        service = self.get_service(service_id, type=type)
        return service.instantiate_prompt_execution_settings(
            service_id=service_id,
            extension_data={"ai_model_id": service.ai_model_id},
        )

    def add_service(self, service: AIServiceClientBase, overwrite: bool = False) -> None:
        if service.service_id not in self.services or overwrite:
            self.services[service.service_id] = service
        else:
            raise KernelFunctionAlreadyExistsError(f"Service with service_id '{service.service_id}' already exists")

    def remove_service(self, service_id: str) -> None:
        """Delete a single service from the Kernel."""
        if service_id not in self.services:
            raise KernelServiceNotFoundError(f"Service with service_id '{service_id}' does not exist")
        del self.services[service_id]

    def remove_all_services(self) -> None:
        """Removes the services from the Kernel, does not delete them."""
        self.services.clear()

    # endregion
