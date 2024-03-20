# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import glob
import importlib
import inspect
import logging
import os
from copy import copy
from typing import Any, AsyncIterable, Callable, Literal, Type, TypeVar

import yaml
from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.events import FunctionInvokedEventArgs, FunctionInvokingEventArgs
from semantic_kernel.exceptions import (
    FunctionInitializationError,
    FunctionNameNotUniqueError,
    KernelFunctionAlreadyExistsError,
    KernelFunctionNotFoundError,
    KernelInvokeException,
    KernelPluginNotFoundError,
    KernelServiceNotFoundError,
    PluginInitializationError,
    PluginInvalidNameError,
    ServiceInvalidRequestError,
    ServiceInvalidTypeError,
    TemplateSyntaxError,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP, KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.const import (
    KERNEL_TEMPLATE_FORMAT_NAME,
    TEMPLATE_FORMAT_TYPES,
)
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.reliability.pass_through_without_retry import PassThroughWithoutRetry
from semantic_kernel.reliability.retry_mechanism_base import RetryMechanismBase
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector
from semantic_kernel.utils.validation import validate_plugin_name

T = TypeVar("T")

ALL_SERVICE_TYPES = "TextCompletionClientBase | ChatCompletionClientBase | EmbeddingGeneratorBase"

logger: logging.Logger = logging.getLogger(__name__)


class Kernel(KernelBaseModel):
    """
    The Kernel class is the main entry point for the Semantic Kernel. It provides the ability to run
    semantic/native functions, and manage plugins, memory, and AI services.

    Attributes:
        plugins (KernelPluginCollection | None): The collection of plugins to be used by the kernel
        services (dict[str, AIServiceClientBase]): The services to be used by the kernel
        retry_mechanism (RetryMechanismBase): The retry mechanism to be used by the kernel
        function_invoking_handlers (dict): The function invoking handlers
        function_invoked_handlers (dict): The function invoked handlers
    """

    # region Init

    plugins: KernelPluginCollection = Field(default_factory=KernelPluginCollection)
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
        plugins: KernelPluginCollection | None = None,
        services: AIServiceClientBase | list[AIServiceClientBase] | dict[str, AIServiceClientBase] | None = None,
        ai_service_selector: AIServiceSelector | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new instance of the Kernel class.

        Args:
            plugins (KernelPluginCollection | None): The collection of plugins to be used by the kernel
            services (AIServiceClientBase | list[AIServiceClientBase] | dict[str, AIServiceClientBase] | None:
                The services to be used by the kernel,
                will be rewritten to a dict with service_id as key
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
            **kwargs,
        }
        if ai_service_selector:
            args["ai_service_selector"] = ai_service_selector
        if plugins:
            args["plugins"] = plugins
        super().__init__(**args)

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
        functions: KernelFunction | list[KernelFunction] | None = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        return_function_results: bool | None = False,
        **kwargs: Any,
    ) -> AsyncIterable[list["StreamingKernelContent"] | list[FunctionResult]]:
        """Execute one or more stream functions.

        This will execute the functions in the order they are provided, if a list of functions is provided.
        When multiple functions are provided only the last one is streamed, the rest is executed as a pipeline.

        Arguments:
            functions (KernelFunction | list[KernelFunction]): The function or functions to execute,
            this value has precedence when supplying both this and using function_name and plugin_name,
            if this is none, function_name and plugin_name are used and cannot be None.
            arguments (KernelArguments): The arguments to pass to the function(s), optional
            function_name (str | None): The name of the function to execute
            plugin_name (str | None): The name of the plugin to execute
            return_function_results (bool | None): If True, the function results are returned in addition to
                the streaming content, otherwise only the streaming content is returned.
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Yields:
            StreamingKernelContent: The content of the stream of the last function provided.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        if not functions:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError("No function(s) or function- and plugin-name provided")
            functions = [self.func(plugin_name, function_name)]
        results: list[FunctionResult] = []
        if isinstance(functions, KernelFunction):
            stream_function = functions
            pipeline_step = 0
        else:
            stream_function = functions[-1]
            if len(functions) > 1:
                pipeline_functions = functions[:-1]
                # run pipeline functions
                result = await self.invoke(functions=pipeline_functions, arguments=arguments)
                # if function was cancelled, the result is None, otherwise can be one or more.
                if result:
                    if isinstance(result, FunctionResult):
                        results.append(result)
                    else:
                        results.extend(result)
            pipeline_step = len(functions) - 1
        while True:
            function_invoking_args = self.on_function_invoking(stream_function.metadata, arguments)
            if function_invoking_args.is_cancel_requested:
                logger.info(
                    f"Execution was cancelled on function invoking event of pipeline step "
                    f"{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                return
            if function_invoking_args.updated_arguments:
                logger.info(
                    f"Arguments updated by function_invoking_handler in pipeline step: "
                    f"{pipeline_step}, new arguments: {function_invoking_args.arguments}"
                )
                arguments = function_invoking_args.arguments
            if function_invoking_args.is_skip_requested:
                logger.info(
                    f"Execution was skipped on function invoking event of pipeline step "
                    f"{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                return
                # TODO: decide how to put results into kernelarguments,
                # might need to be done as part of the invoked_handler
            function_result = []
            exception = None

            async for stream_message in stream_function.invoke_stream(self, arguments):
                if isinstance(stream_message, FunctionResult):
                    exception = stream_message.metadata.get("exception", None)
                    if exception:
                        break
                function_result.append(stream_message)
                yield stream_message

            output_function_result = []
            for result in function_result:
                for choice in result:
                    if len(output_function_result) <= choice.choice_index:
                        output_function_result.append(copy(choice))
                    else:
                        output_function_result[choice.choice_index] += choice
            func_result = FunctionResult(function=stream_function.metadata, value=output_function_result)
            function_invoked_args = self.on_function_invoked(
                stream_function.metadata,
                arguments,
                func_result,
                exception,
            )
            if function_invoked_args.exception:
                raise ServiceInvalidRequestError(
                    f"Something went wrong in stream function. "
                    f"During function invocation:'{stream_function.plugin_name}.{stream_function.name}'. "
                    f"Error description: '{str(function_invoked_args.exception)}'"
                ) from function_invoked_args.exception
            if return_function_results:
                results.append(function_invoked_args.function_result)
            if function_invoked_args.is_cancel_requested:
                logger.info(
                    f"Execution was cancelled on function invoked event of pipeline step "
                    f"{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                return
            if function_invoked_args.updated_arguments:
                logger.info(
                    f"Arguments updated by function_invoked_handler in pipeline step: "
                    f"{pipeline_step}, new arguments: {function_invoked_args.arguments}"
                )
                arguments = function_invoked_args.arguments
            if function_invoked_args.is_repeat_requested:
                logger.info(
                    f"Execution was repeated on function invoked event of pipeline step "
                    f"{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                continue
            break
        if return_function_results:
            yield results

    async def invoke(
        self,
        functions: KernelFunction | list[KernelFunction] | None = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        **kwargs: Any,
    ) -> FunctionResult | list[FunctionResult] | None:
        """Execute one or more functions.

        When multiple functions are passed the FunctionResult of each is put into a list.

        Arguments:
            functions (KernelFunction | list[KernelFunction]): The function or functions to execute,
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
        results = []
        pipeline_step = 0
        if not functions:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError("No function or plugin name provided")
            functions = [self.func(plugin_name, function_name)]
        if not isinstance(functions, list):
            functions = [functions]
            number_of_steps = 1
        else:
            number_of_steps = len(functions)
        for func in functions:
            # While loop is used to repeat the function invocation, if requested
            while True:
                function_invoking_args = self.on_function_invoking(func.metadata, arguments)
                if function_invoking_args.is_cancel_requested:
                    logger.info(
                        f"Execution was cancelled on function invoking event of pipeline step "
                        f"{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    return results if results else None
                if function_invoking_args.updated_arguments:
                    logger.info(
                        f"Arguments updated by function_invoking_handler in pipeline step: "
                        f"{pipeline_step}, new arguments: {function_invoking_args.arguments}"
                    )
                    arguments = function_invoking_args.arguments
                if function_invoking_args.is_skip_requested:
                    logger.info(
                        f"Execution was skipped on function invoking event of pipeline step "
                        f"{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    break
                function_result = None
                exception = None
                try:
                    function_result = await func.invoke(self, arguments)
                except Exception as exc:
                    logger.error(
                        "Something went wrong in function invocation. During function invocation:"
                        f" '{func.plugin_name}.{func.name}'. Error description: '{str(exc)}'"
                    )
                    exception = exc

                # this allows a hook to alter the results before adding.
                function_invoked_args = self.on_function_invoked(func.metadata, arguments, function_result, exception)
                results.append(function_invoked_args.function_result)

                if function_invoked_args.exception:
                    raise KernelInvokeException(
                        f"Error occurred while invoking function: '{func.plugin_name}.{func.name}'"
                    ) from function_invoked_args.exception
                if function_invoked_args.is_cancel_requested:
                    logger.info(
                        f"Execution was cancelled on function invoked event of pipeline step "
                        f"{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    return results if results else None
                if function_invoked_args.updated_arguments:
                    logger.info(
                        f"Arguments updated by function_invoked_handler in pipeline step: "
                        f"{pipeline_step}, new arguments: {function_invoked_args.arguments}"
                    )
                    arguments = function_invoked_args.arguments
                if function_invoked_args.is_repeat_requested:
                    logger.info(
                        f"Execution was repeated on function invoked event of pipeline step "
                        f"{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    continue
                break

            pipeline_step += 1

        return results if number_of_steps > 1 else results[0]

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
    ) -> FunctionResult | list[FunctionResult] | None:
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

        function = KernelFunctionFromPrompt(
            function_name=function_name,
            plugin_name=plugin_name,
            prompt=prompt,
            template_format=template_format,
        )
        return await self.invoke(functions=function, arguments=arguments)

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
    # region Plugins

    def add_plugin(self, plugin_name: str, functions: list[KernelFunction], plugin: KernelPlugin | None = None) -> None:
        """
        Adds a plugin to the kernel's collection of plugins. If a plugin instance is provided,
        it uses that instance instead of creating a new KernelPlugin.

        Args:
            plugin_name (str): The name of the plugin
            functions (list[KernelFunction]): The functions to add to the plugin
            plugin (KernelPlugin | None): An optional pre-defined plugin instance
        """
        if plugin is None:
            # If no plugin instance is provided, create a new KernelPlugin
            plugin = KernelPlugin(name=plugin_name, functions=functions)

        if plugin_name in self.plugins:
            self.plugins.add_functions_to_plugin(functions=functions, plugin_name=plugin_name)
        else:
            self.plugins.add(plugin)

    def import_plugin_from_object(self, plugin_instance: Any | dict[str, Any], plugin_name: str) -> KernelPlugin:
        """
        Creates a plugin that wraps the specified target object and imports it into the kernel's plugin collection

        Args:
            plugin_instance (Any | dict[str, Any]): The plugin instance. This can be a custom class or a
                dictionary of classes that contains methods with the kernel_function decorator for one or
                several methods. See `TextMemoryPlugin` as an example.
            plugin_name (str): The name of the plugin. Allows chars: upper, lower ASCII and underscores.

        Returns:
            KernelPlugin: The imported plugin of type KernelPlugin.
        """
        if not plugin_name.strip():
            raise PluginInvalidNameError("Plugin name cannot be empty")
        logger.debug(f"Importing plugin {plugin_name}")

        functions: dict[str, KernelFunction] = {}

        if isinstance(plugin_instance, dict):
            candidates = plugin_instance.items()
        else:
            candidates = inspect.getmembers(plugin_instance, inspect.ismethod)
        # Read every method from the plugin instance
        for _, candidate in candidates:
            # If the method is a prompt function, register it
            if not hasattr(candidate, "__kernel_function__"):
                continue

            func = KernelFunctionFromMethod(plugin_name=plugin_name, method=candidate)
            if func.name in functions:
                raise FunctionNameNotUniqueError(
                    "Overloaded functions are not supported, " "please differentiate function names."
                )
            functions[func.name] = func
        logger.debug(f"Methods imported: {len(functions)}")

        plugin = KernelPlugin(name=plugin_name, functions=functions)
        self.plugins.add(plugin)

        return plugin

    def import_native_plugin_from_directory(self, parent_directory: str, plugin_directory_name: str) -> KernelPlugin:
        MODULE_NAME = "native_function"

        validate_plugin_name(plugin_directory_name)

        plugin_directory = os.path.abspath(os.path.join(parent_directory, plugin_directory_name))
        native_py_file_path = os.path.join(plugin_directory, f"{MODULE_NAME}.py")

        if not os.path.exists(native_py_file_path):
            raise PluginInitializationError(f"Native Plugin Python File does not exist: {native_py_file_path}")

        plugin_name = os.path.basename(plugin_directory)

        spec = importlib.util.spec_from_file_location(MODULE_NAME, native_py_file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class_name = next(
            (name for name, cls in inspect.getmembers(module, inspect.isclass) if cls.__module__ == MODULE_NAME),
            None,
        )
        if class_name:
            plugin_obj = getattr(module, class_name)()
            return self.import_plugin_from_object(plugin_obj, plugin_name)

        return None

    def import_plugin_from_prompt_directory(self, parent_directory: str, plugin_directory_name: str) -> KernelPlugin:
        """
        Import a plugin from a specified directory, processing both YAML files and subdirectories
        containing `skprompt.txt` and `config.json` files to create KernelFunction objects. These objects
        are then grouped into a single KernelPlugin instance.

        This method does not recurse into subdirectories beyond one level deep from the specified plugin directory.
        For YAML files, function names are extracted from the content of the YAML files themselves (the name property).
        For directories, the function name is assumed to be the name of the directory. Each KernelFunction object is
        initialized with data parsed from the associated files and added to a list of functions that are then assigned
        to the created KernelPlugin object.

        Args:
            parent_directory (str): The parent directory path where the plugin directory resides. This should be
                an absolute path to ensure correct file resolution.
            plugin_directory_name (str): The name of the directory that contains the plugin's YAML files and
                subdirectories. This directory name is used as the plugin name and should be directly under the
                parent_directory.

        Returns:
            KernelPlugin: An instance of KernelPlugin containing all the KernelFunction objects created from
                the YAML files and directories found in the specified plugin directory. The name of the
                plugin is set to the plugin_directory_name.

        Raises:
            PluginInitializationError: If the plugin directory does not exist.
            PluginInvalidNameError: If the plugin name is invalid.

        Example:
            Assuming a plugin directory structure as follows:

            MyPlugins/
            |--- pluginA.yaml
            |--- pluginB.yaml
            |--- Directory1/
                |--- skprompt.txt
                |--- config.json
            |--- Directory2/
                |--- skprompt.txt
                |--- config.json

            Calling `import_plugin("/path/to", "MyPlugins")` will create a KernelPlugin object named
                "MyPlugins", containing KernelFunction objects for `pluginA.yaml`, `pluginB.yaml`,
                `Directory1`, and `Directory2`, each initialized with their respective configurations.
        """
        plugin_directory = self._validate_plugin_directory(
            parent_directory=parent_directory, plugin_directory_name=plugin_directory_name
        )

        functions = []

        # Handle YAML files at the root
        yaml_files = glob.glob(os.path.join(plugin_directory, "*.yaml"))
        for yaml_file in yaml_files:
            with open(yaml_file, "r") as file:
                yaml_content = file.read()
                functions.append(self.create_function_from_yaml(yaml_content, plugin_name=plugin_directory_name))

        # Handle directories containing skprompt.txt and config.json
        for item in os.listdir(plugin_directory):
            item_path = os.path.join(plugin_directory, item)
            if os.path.isdir(item_path):
                prompt_path = os.path.join(item_path, "skprompt.txt")
                config_path = os.path.join(item_path, "config.json")

                if os.path.exists(prompt_path) and os.path.exists(config_path):
                    with open(config_path, "r") as config_file:
                        prompt_template_config = PromptTemplateConfig.from_json(config_file.read())
                    prompt_template_config.name = item

                    with open(prompt_path, "r") as prompt_file:
                        prompt = prompt_file.read()
                        prompt_template_config.template = prompt

                    prompt_template = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                        prompt_template_config=prompt_template_config
                    )

                    functions.append(
                        self.create_function_from_prompt(
                            plugin_name=plugin_directory_name,
                            prompt_template=prompt_template,
                            prompt_template_config=prompt_template_config,
                            template_format=prompt_template_config.template_format,
                            function_name=item,
                            description=prompt_template_config.description,
                        )
                    )

        return KernelPlugin(name=plugin_directory_name, functions=functions)

    def _validate_plugin_directory(self, parent_directory: str, plugin_directory_name: str) -> str:
        """Validate the plugin name and that the plugin directory exists.

        Args:
            parent_directory (str): The parent directory
            plugin_directory_name (str): The plugin directory name

        Returns:
            str: The plugin directory.

        Raises:
            PluginInitializationError: If the plugin directory does not exist.
            PluginInvalidNameError: If the plugin name is invalid.
        """
        validate_plugin_name(plugin_directory_name)

        plugin_directory = os.path.join(parent_directory, plugin_directory_name)
        plugin_directory = os.path.abspath(plugin_directory)

        if not os.path.exists(plugin_directory):
            raise PluginInitializationError(f"Plugin directory does not exist: {plugin_directory_name}")

        return plugin_directory

    # endregion
    # region Functions

    def func(self, plugin_name: str, function_name: str) -> KernelFunction:
        if plugin_name not in self.plugins:
            raise KernelPluginNotFoundError(f"Plugin '{plugin_name}' not found")
        if function_name not in self.plugins[plugin_name]:
            raise KernelFunctionNotFoundError(f"Function '{function_name}' not found in plugin '{plugin_name}'")
        return self.plugins[plugin_name][function_name]

    def func_from_fully_qualified_function_name(self, fully_qualified_function_name: str) -> KernelFunction:
        plugin_name, function_name = fully_qualified_function_name.split("-")
        if plugin_name not in self.plugins:
            raise KernelPluginNotFoundError(f"Plugin '{plugin_name}' not found")
        if function_name not in self.plugins[plugin_name]:
            raise KernelFunctionNotFoundError(f"Function '{function_name}' not found in plugin '{plugin_name}'")
        return self.plugins[plugin_name][function_name]

    def create_function_from_prompt(
        self,
        function_name: str,
        plugin_name: str,
        description: str | None = None,
        prompt: str | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        prompt_execution_settings: (
            PromptExecutionSettings | list[PromptExecutionSettings] | dict[str, PromptExecutionSettings] | None
        ) = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: PromptTemplateBase | None = None,
        **kwargs: Any,
    ) -> KernelFunction:
        """
        Create a Kernel Function from a prompt.

        Args:
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
            kwargs (Any): Additional arguments

        Returns:
            KernelFunction: The created Kernel Function
        """
        if prompt_execution_settings is None and (
            prompt_template_config is None or prompt_template_config.execution_settings is None
        ):
            prompt_execution_settings = PromptExecutionSettings(extension_data=kwargs)

        function = KernelFunctionFromPrompt(
            function_name=function_name,
            plugin_name=plugin_name,
            description=description,
            prompt=prompt,
            template_format=template_format,
            prompt_template=prompt_template,
            prompt_template_config=prompt_template_config,
            prompt_execution_settings=prompt_execution_settings,
        )

        self.add_plugin(plugin_name or function.plugin_name, [function])

        return function

    def create_function_from_yaml(self, text: str, plugin_name: str) -> KernelFunction:
        """
        Import a plugin from a YAML string.

        Args:
            text (str): The YAML string

        Returns:
            KernelFunction: The created Kernel Function

        Raises:
            PluginInitializationError: If the input YAML string is empty
        """
        if not text:
            raise PluginInitializationError("The input YAML string is empty")

        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise PluginInitializationError(f"Error loading YAML: {exc}") from exc

        if not isinstance(data, dict):
            raise PluginInitializationError("The YAML content must represent a dictionary")

        try:
            prompt_template_config = PromptTemplateConfig(**data)
        except TypeError as exc:
            raise PluginInitializationError(f"Error initializing PromptTemplateConfig: {exc}") from exc

        return self.create_function_from_prompt(
            function_name=prompt_template_config.name,
            plugin_name=plugin_name,
            description=prompt_template_config.description,
            prompt_template_config=prompt_template_config,
            template_format=prompt_template_config.template_format,
        )

    def register_function_from_method(
        self,
        plugin_name: str,
        method: Callable[..., Any],
    ) -> KernelFunction:
        """
        Creates a native function from the plugin name and registers it with the kernel.

        Args:
            plugin_name (str | None): The name of the plugin. If empty, a random name will be generated.
            kernel_function (Callable): The kernel function

        Returns:
            KernelFunction: The created native function
        """
        if not hasattr(method, "__kernel_function__"):
            raise FunctionInitializationError(
                "kernel_function argument must be decorated with @kernel_function",
            )

        function = KernelFunctionFromMethod(
            method=method,
            plugin_name=plugin_name,
        )
        self.add_plugin(plugin_name or function.plugin_name, [function])

        return function

    # endregion
    # region Services

    def select_ai_service(
        self, function: KernelFunction, arguments: KernelArguments
    ) -> tuple[ALL_SERVICE_TYPES, PromptExecutionSettings]:
        """Uses the AI service selector to select a service for the function."""
        return self.ai_service_selector.select_ai_service(self, function, arguments)

    def get_service(
        self,
        service_id: str | None = None,
        type: Type[ALL_SERVICE_TYPES] | None = None,
    ) -> ALL_SERVICE_TYPES:
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

    def get_services_by_type(self, type: Type[T]) -> dict[str, T]:
        return {service.service_id: service for service in self.services.values() if isinstance(service, type)}

    def get_prompt_execution_settings_from_service_id(
        self, service_id: str, type: Type[T] | None = None
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
