# Copyright (c) Microsoft. All rights reserved.

import glob
import importlib
import inspect
import logging
import os
from copy import copy
from typing import Any, AsyncIterable, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import Field

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.events import FunctionInvokedEventArgs, FunctionInvokingEventArgs
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import (
    KernelPluginCollection,
)
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.reliability.pass_through_without_retry import (
    PassThroughWithoutRetry,
)
from semantic_kernel.reliability.retry_mechanism_base import RetryMechanismBase
from semantic_kernel.services.ai_service_selector import get_ai_service
from semantic_kernel.template_engine.prompt_template_engine import PromptTemplateEngine
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)
from semantic_kernel.utils.naming import generate_random_ascii_name
from semantic_kernel.utils.validation import (
    validate_function_name,
    validate_plugin_name,
)

T = TypeVar("T")

logger: logging.Logger = logging.getLogger(__name__)


class Kernel(KernelBaseModel):
    """
    The Kernel class is the main entry point for the Semantic Kernel. It provides the ability to run
    semantic/native functions, and manage plugins, memory, and AI services.

    Attributes:
        plugins (Optional[KernelPluginCollection]): The collection of plugins to be used by the kernel
        prompt_template_engine (Optional[PromptTemplatingEngine]): The prompt template engine to be used by the kernel
        memory (Optional[SemanticTextMemoryBase]): The memory to be used by the kernel
        text_completion_services (Dict[str, Callable[["Kernel"], TextCompletionClientBase]]): The text
            completion services
        chat_services (Dict[str, Callable[["Kernel"], ChatCompletionClientBase]]): The chat services
        text_embedding_generation_services (Dict[str, Callable[["Kernel"], EmbeddingGeneratorBase]]): The text embedding
        default_text_completion_service (Optional[str]): The default text completion service
        default_chat_service (Optional[str]): The default chat service
        default_text_embedding_generation_service (Optional[str]): The default text embedding generation service
        retry_mechanism (RetryMechanismBase): The retry mechanism to be used by the kernel
        function_invoking_handlers (Dict): The function invoking handlers
        function_invoked_handlers (Dict): The function invoked handlers
    """

    plugins: Optional[KernelPluginCollection] = Field(default_factory=KernelPluginCollection)
    prompt_template_engine: Optional[PromptTemplatingEngine] = Field(default_factory=PromptTemplateEngine)
    memory: Optional[SemanticTextMemoryBase] = Field(default_factory=SemanticTextMemory)
    text_completion_services: Dict[str, Callable[["Kernel"], TextCompletionClientBase]] = Field(default_factory=dict)
    chat_services: Dict[str, Callable[["Kernel"], ChatCompletionClientBase]] = Field(default_factory=dict)
    text_embedding_generation_services: Dict[str, Callable[["Kernel"], EmbeddingGeneratorBase]] = Field(
        default_factory=dict
    )
    default_text_completion_service: Optional[str] = Field(default=None)
    default_chat_service: Optional[str] = Field(default=None)
    default_text_embedding_generation_service: Optional[str] = Field(default=None)
    retry_mechanism: RetryMechanismBase = Field(default_factory=PassThroughWithoutRetry)
    function_invoking_handlers: Dict = Field(default_factory=dict)
    function_invoked_handlers: Dict = Field(default_factory=dict)

    def __init__(
        self,
        plugins: Optional[KernelPluginCollection] = None,
        prompt_template_engine: Optional[PromptTemplatingEngine] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a new instance of the Kernel class.

        Args:
            plugins (Optional[KernelPluginCollection]): The collection of plugins to be used by the kernel
            prompt_template_engine (Optional[PromptTemplatingEngine]): The prompt template engine to be
                used by the kernel
            memory (Optional[SemanticTextMemoryBase]): The memory to be used by the kernel
            **kwargs (Any): Additional fields to be passed to the Kernel model
        """
        plugins = plugins if plugins else KernelPluginCollection()
        prompt_template_engine = prompt_template_engine if prompt_template_engine else PromptTemplatingEngine()
        memory = memory if memory else NullMemory()

        super().__init__(plugins=plugins, prompt_template_engine=prompt_template_engine, memory=memory, **kwargs)

    def add_plugin(
        self, plugin_name: str, functions: List[KernelFunction], plugin: Optional[KernelPlugin] = None
    ) -> None:
        """
        Adds a plugin to the kernel's collection of plugins. If a plugin instance is provided,
        it uses that instance instead of creating a new KernelPlugin.

        Args:
            plugin_name (str): The name of the plugin
            functions (List[KernelFunction]): The functions to add to the plugin
            plugin (Optional[KernelPlugin]): An optional pre-defined plugin instance
        """
        if plugin is None:
            # If no plugin instance is provided, create a new KernelPlugin
            plugin = KernelPlugin(name=plugin_name, functions=functions)

        if plugin_name in self.plugins:
            self.plugins.add_functions_to_plugin(functions=functions, plugin_name=plugin_name)
        else:
            self.plugins.add(plugin)

    def create_function_from_prompt(
        self,
        template: Optional[str] = None,
        prompt_template_config: Optional[PromptTemplateConfig] = None,
        execution_settings: Optional[PromptExecutionSettings] = None,
        function_name: Optional[str] = None,
        plugin_name: Optional[str] = None,
        description: Optional[str] = None,
        template_format: Optional[str] = None,
        prompt_template: Optional[PromptTemplateBase] = None,
    ) -> KernelFunction:
        """
        Create a Kernel Function from a prompt.

        Args:
            template (Optional[str]): The prompt template
            prompt_template_config (Optional[PromptTemplateConfig]): The prompt template configuration
            execution_settings (Optional[PromptExecutionSettings]): The execution settings
            function_name (Optional[str]): The name of the function
            plugin_name (Optional[str]): The name of the plugin
            description (Optional[str]): The description of the function
            template_format (Optional[str]): The format of the prompt template
            prompt_template (Optional[PromptTemplateBase]): The prompt template

        Returns:
            KernelFunction: The created Kernel Function
        """
        if not plugin_name:
            plugin_name = f"p_{generate_random_ascii_name()}"
        assert plugin_name is not None  # for type checker

        if not function_name:
            function_name = f"f_{generate_random_ascii_name()}"
        assert function_name is not None  # for type checker

        validate_plugin_name(plugin_name)
        validate_function_name(function_name)

        function = KernelFunction.from_prompt(
            prompt=template,
            execution_settings=execution_settings,
            function_name=function_name,
            plugin_name=plugin_name,
            description=description,
            template_format=template_format,
            prompt_template=prompt_template,
            prompt_template_config=prompt_template_config,
        )

        # TODO: Can this `get_ai_service` call be moved to the function invoke?
        service, _, service_base_type = get_ai_service(self, function, KernelArguments())
        if service is None:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                (f"Could not load AI service for: {function.plugin_name}.{function.name}"),
            )

        if not execution_settings:
            execution_settings = function.prompt_execution_settings

        if issubclass(service_base_type, ChatCompletionClientBase):
            req_settings_type = service.__closure__[0].cell_contents.get_prompt_execution_settings_class()
            exec_settings = req_settings_type.from_prompt_execution_settings(
                execution_settings["default"]
            )  # TODO, make dynamic
            function.set_chat_configuration({"default": exec_settings})
            function.set_chat_service(lambda: service(self))
        elif issubclass(service_base_type, TextCompletionClientBase):
            req_settings_type = service.__closure__[0].cell_contents.get_prompt_execution_settings_class()
            exec_settings = req_settings_type.from_prompt_execution_settings(
                execution_settings["default"]
            )  # TODO, make dynamic
            function.set_ai_configuration({"default": exec_settings})
            function.set_ai_service(lambda: service(self))
        else:
            raise ValueError(f"Unknown AI service type: {service.__name__}")

        self.add_plugin(plugin_name, [function])
        function.set_default_plugin_collection(self.plugins)

        return function

    def register_native_function(
        self,
        plugin_name: Optional[str],
        kernel_function: Callable,
    ) -> KernelFunction:
        """
        Creates a native function from the plugin name and kernel function

        Args:
            plugin_name (Optional[str]): The name of the plugin. If empty, a random name will be generated.
            kernel_function (Callable): The kernel function

        Returns:
            KernelFunction: The created native function
        """
        if not hasattr(kernel_function, "__kernel_function__"):
            raise KernelException(
                KernelException.ErrorCodes.InvalidFunctionType,
                "kernel_function argument must be decorated with @kernel_function",
            )
        function_name = kernel_function.__kernel_function_name__

        if plugin_name is None or plugin_name == "":
            plugin_name = f"p_{generate_random_ascii_name()}"
        assert plugin_name is not None  # for type checker

        validate_plugin_name(plugin_name)
        validate_function_name(function_name)

        if plugin_name in self.plugins and function_name in self.plugins[plugin_name]:
            raise KernelException(
                KernelException.ErrorCodes.FunctionOverloadNotSupported,
                "Overloaded functions are not supported, " "please differentiate function names.",
            )

        function = KernelFunction.from_native_method(kernel_function, plugin_name)
        self.add_plugin(plugin_name, [function])
        function.set_default_plugin_collection(self.plugins)

        return function

    async def invoke_stream(
        self,
        functions: Union[KernelFunction, List[KernelFunction]],
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> AsyncIterable[List["StreamingKernelContent"]]:
        """Execute one or more stream functions.

        This will execute the functions in the order they are provided, if a list of functions is provided.
        When multiple functions are provided only the last one is streamed, the rest is executed as a pipeline.

        Arguments:
            functions (Union[KernelFunction, List[KernelFunction]]): The function or functions to execute
            arguments (KernelArguments): The arguments to pass to the function(s), optional
            kwargs (Dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Yields:
            StreamingKernelContent: The content of the stream of the last function provided.
        """
        if not arguments:
            arguments = KernelArguments(**kwargs)
        if isinstance(functions, KernelFunction):
            stream_function = functions
            results = []
            pipeline_step = 0
        else:
            stream_function = functions[-1]
            if len(functions) > 1:
                pipeline_functions = functions[:-1]
                # run pipeline functions
                results = await self.invoke(pipeline_functions, arguments)
            else:
                raise ValueError("No functions passed to run")
            if not results:
                results = []
            pipeline_step = len(functions) - 1
        while True:
            function_invoking_args = self.on_function_invoking(stream_function.describe(), arguments)
            if function_invoking_args.is_cancel_requested:
                logger.info(
                    f"Execution was cancelled on function invoking event of pipeline step \
{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                return
            if function_invoking_args.updated_arguments:
                logger.info(
                    f"Arguments updated by function_invoking_handler in pipeline step: \
{pipeline_step}, new arguments: {function_invoking_args.arguments}"
                )
                arguments = function_invoking_args.arguments
            if function_invoking_args.is_skip_requested:
                logger.info(
                    f"Execution was skipped on function invoking event of pipeline step \
{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                return
                # TODO: decide how to put results into kernelarguments,
                # might need to be done as part of the invoked_handler
            function_result = []
            exception = None
            try:
                async for stream_message in stream_function.invoke_stream(self, arguments):
                    if isinstance(stream_message, FunctionResult):
                        err_msg = stream_message.metadata.get("error", None)
                        exception = Exception(f"Error occurred in stream function: {err_msg}")
                    function_result.append(stream_message)
                    yield stream_message
            except Exception as exc:
                logger.error(
                    "Something went wrong in stream function. During function invocation:"
                    f" '{stream_function.plugin_name}.{stream_function.name}'. Error"
                    f" description: '{str(exc)}'"
                )
                exception = exc
            # TODO: process function_result list to FunctionResult
            output_function_result = []
            for result in function_result:
                for index, choice in enumerate(result):
                    if len(output_function_result) <= index:
                        output_function_result.append(copy(choice))
                    else:
                        output_function_result[index] += choice
            func_result = FunctionResult(function=stream_function.describe(), value=output_function_result)
            function_invoked_args = self.on_function_invoked(
                stream_function.describe(),
                arguments,
                func_result,
                exception,
            )
            results.append(function_invoked_args.function_result)
            if function_invoked_args.exception:
                raise KernelException(
                    KernelException.ErrorCodes.FunctionInvokeError,
                    "Error occurred while invoking stream function",
                    function_invoked_args.exception,
                ) from function_invoked_args.exception

            if function_invoked_args.is_cancel_requested:
                logger.info(
                    f"Execution was cancelled on function invoked event of pipeline step \
{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                return
            if function_invoked_args.updated_arguments:
                logger.info(
                    f"Arguments updated by function_invoked_handler in pipeline step: \
{pipeline_step}, new arguments: {function_invoked_args.arguments}"
                )
                arguments = function_invoked_args.arguments
            if function_invoked_args.is_repeat_requested:
                logger.info(
                    f"Execution was repeated on function invoked event of pipeline step \
{pipeline_step}: {stream_function.plugin_name}.{stream_function.name}."
                )
                continue
            break

    async def invoke(
        self,
        functions: Union[KernelFunction, List[KernelFunction]],
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> Optional[Union[FunctionResult, List[FunctionResult]]]:
        """Execute one or more functions.

        When multiple functions are passed the FunctionResult of each is put into a list.

        Arguments:
            functions (Union[KernelFunction, List[KernelFunction]]): The function or functions to execute
            arguments (KernelArguments): The arguments to pass to the function(s), optional
            kwargs (Dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Returns:
            Optional[Union[FunctionResult, List[FunctionResult]]]: The result of the function(s)

        """
        if not arguments:
            arguments = KernelArguments(**kwargs)
        results = []
        pipeline_step = 0
        if not isinstance(functions, list):
            functions = [functions]
            number_of_steps = 1
        else:
            number_of_steps = len(functions)
        for func in functions:
            # While loop is used to repeat the function invocation, if requested
            while True:
                function_invoking_args = self.on_function_invoking(func.describe(), arguments)
                if function_invoking_args.is_cancel_requested:
                    logger.info(
                        f"Execution was cancelled on function invoking event of pipeline step \
{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    return results if results else None
                if function_invoking_args.updated_arguments:
                    logger.info(
                        f"Arguments updated by function_invoking_handler in pipeline step: \
{pipeline_step}, new arguments: {function_invoking_args.arguments}"
                    )
                    arguments = function_invoking_args.arguments
                if function_invoking_args.is_skip_requested:
                    logger.info(
                        f"Execution was skipped on function invoking event of pipeline step \
{pipeline_step}: {func.plugin_name}.{func.name}."
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
                function_invoked_args = self.on_function_invoked(func.describe(), arguments, function_result, exception)
                results.append(function_invoked_args.function_result)

                if function_invoked_args.exception:
                    raise KernelException(
                        KernelException.ErrorCodes.FunctionInvokeError,
                        f"Error occurred while invoking function: '{func.plugin_name}.{func.name}'",
                        function_invoked_args.exception,
                    ) from function_invoked_args.exception
                if function_invoked_args.is_cancel_requested:
                    logger.info(
                        f"Execution was cancelled on function invoked event of pipeline step \
{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    return results if results else None
                if function_invoked_args.updated_arguments:
                    logger.info(
                        f"Arguments updated by function_invoked_handler in pipeline step: \
{pipeline_step}, new arguments: {function_invoked_args.arguments}"
                    )
                    arguments = function_invoked_args.arguments
                if function_invoked_args.is_repeat_requested:
                    logger.info(
                        f"Execution was repeated on function invoked event of pipeline step \
{pipeline_step}: {func.plugin_name}.{func.name}."
                    )
                    continue
                break

            pipeline_step += 1

        return results if number_of_steps > 1 else results[0]

    def func(self, plugin_name: str, function_name: str) -> KernelFunction:
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        if function_name not in self.plugins[plugin_name]:
            raise ValueError(f"Function '{function_name}' not found in plugin '{plugin_name}'")
        return self.plugins[plugin_name][function_name]

    def use_memory(
        self,
        storage: MemoryStoreBase,
        embeddings_generator: Optional[EmbeddingGeneratorBase] = None,
    ) -> None:
        if embeddings_generator is None:
            service_id = self.get_text_embedding_generation_service_id()
            if not service_id:
                raise ValueError("The embedding service id cannot be `None` or empty")

            embeddings_service = self.get_ai_service(EmbeddingGeneratorBase, service_id)
            if not embeddings_service:
                raise ValueError(f"AI configuration is missing for: {service_id}")

            embeddings_generator = embeddings_service(self)

        if storage is None:
            raise ValueError("The storage instance provided cannot be `None`")
        if embeddings_generator is None:
            raise ValueError("The embedding generator cannot be `None`")

        self.register_memory(SemanticTextMemory(storage, embeddings_generator))

    def register_memory(self, memory: SemanticTextMemoryBase) -> None:
        self.memory = memory

    def register_memory_store(self, memory_store: MemoryStoreBase) -> None:
        self.use_memory(memory_store)

    def on_function_invoking(
        self, kernel_function_metadata: KernelFunctionMetadata, arguments: KernelArguments
    ) -> FunctionInvokingEventArgs:
        args = FunctionInvokingEventArgs(kernel_function_metadata=kernel_function_metadata, arguments=arguments)
        if self.function_invoking_handlers:
            for handler in self.function_invoking_handlers.values():
                handler(self, args)
        return args

    def on_function_invoked(
        self,
        kernel_function_metadata: KernelFunctionMetadata,
        arguments: KernelArguments,
        function_result: Optional[FunctionResult] = None,
        exception: Optional[Exception] = None,
    ) -> FunctionInvokedEventArgs:
        # TODO: include logic that uses function_result
        args = FunctionInvokedEventArgs(
            kernel_function_metadata=kernel_function_metadata,
            arguments=arguments,
            function_result=function_result,
            exception=exception,
        )
        if self.function_invoked_handlers:
            for handler in self.function_invoked_handlers.values():
                handler(self, args)
        return args

    def import_plugin(self, plugin_instance: Union[Any, Dict[str, Any]], plugin_name: str) -> KernelPlugin:
        """
        Import a plugin into the kernel.

        Args:
            plugin_instance (Any | Dict[str, Any]): The plugin instance. This can be a custom class or a
                dictionary of classes that contains methods with the kernel_function decorator for one or
                several methods. See `TextMemoryPlugin` as an example.
            plugin_name (str): The name of the plugin. Allows chars: upper, lower ASCII and underscores.

        Returns:
            KernelPlugin: The imported plugin of type KernelPlugin.
        """
        if not plugin_name.strip():
            logger.warn("Unable to import plugin due to missing plugin_name")
            raise KernelException(
                KernelException.ErrorCodes.InvalidPluginName,
                "Plugin name cannot be empty",
            )
        logger.debug(f"Importing plugin {plugin_name}")

        functions = []

        if isinstance(plugin_instance, dict):
            candidates = plugin_instance.items()
        else:
            candidates = inspect.getmembers(plugin_instance, inspect.ismethod)
        # Read every method from the plugin instance
        for _, candidate in candidates:
            # If the method is a prompt function, register it
            if not hasattr(candidate, "__kernel_function__"):
                continue

            functions.append(KernelFunction.from_native_method(candidate, plugin_name))

        logger.debug(f"Methods imported: {len(functions)}")

        # Uniqueness check on function names
        function_names = [f.name for f in functions]
        if len(function_names) != len(set(function_names)):
            raise KernelException(
                KernelException.ErrorCodes.FunctionOverloadNotSupported,
                ("Overloaded functions are not supported, " "please differentiate function names."),
            )

        # This is legacy - figure out why we're setting all plugins on each function?
        for func in functions:
            func.set_default_plugin_collection(self.plugins)

        plugin = KernelPlugin(name=plugin_name, functions=functions)
        # TODO: we shouldn't have to be adding functions to a plugin after the fact
        # This isn't done in dotnet, and needs to be revisited as we move to v1.0
        # This is to support the current state of the code
        if plugin_name in self.plugins:
            self.plugins.add_functions_to_plugin(functions=functions, plugin_name=plugin_name)
        else:
            self.plugins.add(plugin)

        return plugin

    def get_prompt_execution_settings_from_service(
        self, type: Type[T], service_id: Optional[str] = None
    ) -> PromptExecutionSettings:
        """Get the specific request settings from the service, instantiated with the service_id and ai_model_id."""
        service = self.get_ai_service(type, service_id)
        service_instance = service.__closure__[0].cell_contents
        req_settings_type = service_instance.get_prompt_execution_settings_class()
        return req_settings_type(
            service_id=service_id,
            extension_data={"ai_model_id": service_instance.ai_model_id},
        )

    def get_ai_service(self, type: Type[T], service_id: Optional[str] = None) -> Callable[["Kernel"], T]:
        matching_type = {}
        if type == TextCompletionClientBase:
            service_id = service_id or self.default_text_completion_service
            matching_type = self.text_completion_services
        elif type == ChatCompletionClientBase:
            service_id = service_id or self.default_chat_service
            matching_type = self.chat_services
        elif type == EmbeddingGeneratorBase:
            service_id = service_id or self.default_text_embedding_generation_service
            matching_type = self.text_embedding_generation_services
        else:
            raise ValueError(f"Unknown AI service type: {type.__name__}")

        if service_id not in matching_type:
            raise ValueError(f"{type.__name__} service with service_id '{service_id}' not found")

        return matching_type[service_id]

    def all_text_completion_services(self) -> List[str]:
        return list(self.text_completion_services.keys())

    def all_text_completion_services_with_types(self) -> List[Tuple[str, Type[TextCompletionClientBase]]]:
        """
        Returns a list of tuples, each containing the key and the type of a text completion service.

        Returns:
        A list of tuples (service_id, service_type).
        """
        services_with_types = []
        for service_id in self.text_completion_services.keys():
            service_type = self.get_service_type(self.text_completion_services, service_id)
            if service_type is not None:
                services_with_types.append((service_id, service_type))

        return services_with_types

    def all_chat_services(self) -> List[str]:
        return list(self.chat_services.keys())

    def all_chat_services_with_types(self) -> List[Tuple[str, Type[ChatCompletionClientBase]]]:
        """
        Returns a list of tuples, each containing the key and the type of a chat service.

        Returns:
        A list of tuples (service_id, service_type).
        """
        services_with_types = []
        for service_id in self.chat_services.keys():
            service_type = self.get_service_type(self.chat_services, service_id)
            if service_type is not None:
                services_with_types.append((service_id, service_type))

        return services_with_types

    def all_text_embedding_generation_services(self) -> List[str]:
        return list(self.text_embedding_generation_services.keys())

    def all_text_embedding_generation_services_with_types(self) -> List[Tuple[str, Type[ChatCompletionClientBase]]]:
        """
        Returns a list of tuples, each containing the key and the type of a chat service.

        Returns:
        A list of tuples (service_id, service_type).
        """
        services_with_types = []
        for service_id in self.chat_services.keys():
            service_type = self.get_service_type(self.text_embedding_generation_services, service_id)
            if service_type is not None:
                services_with_types.append((service_id, service_type))

        return services_with_types

    def add_default_values(self, arguments, prompt_template_config):
        for parameter in prompt_template_config.input_variables:
            # if parameter.name not in arguments and not parameter.default:
            if not arguments.get(parameter.name) and parameter.default not in {None, "", False, 0}:
                arguments[parameter.name] = parameter.default

    def add_text_completion_service(
        self,
        service_id: str,
        service: Union[TextCompletionClientBase, Callable[["Kernel"], TextCompletionClientBase]],
        overwrite: bool = True,
    ) -> "Kernel":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self.text_completion_services:
            raise ValueError(f"Text service with service_id '{service_id}' already exists")

        self.text_completion_services[service_id] = service if isinstance(service, Callable) else lambda _: service
        if self.default_text_completion_service is None:
            self.default_text_completion_service = service_id

        return self

    def add_chat_service(
        self,
        service_id: str,
        service: Union[ChatCompletionClientBase, Callable[["Kernel"], ChatCompletionClientBase]],
        overwrite: bool = True,
    ) -> "Kernel":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self.chat_services:
            raise ValueError(f"Chat service with service_id '{service_id}' already exists")

        self.chat_services[service_id] = service if isinstance(service, Callable) else lambda _: service
        if self.default_chat_service is None:
            self.default_chat_service = service_id

        if isinstance(service, TextCompletionClientBase):
            self.add_text_completion_service(service_id, service)

        return self

    def get_service_type(self, service_type: Any, service_id: str) -> Union[Type[ChatCompletionClientBase], None]:
        """
        Get the type of a chat service stored in chat_services.

        Parameters:
        - service_id: The ID of the chat service.

        Returns:
        The type of the chat service if found, otherwise None.
        """
        service = service_type.get(service_id)
        if service is None:
            return None

        if isinstance(service, Callable):
            try:
                service_instance = service(self)  # Assuming 'self' is a valid Kernel instance
                return type(service_instance)
            except Exception as e:
                print(f"Error instantiating service from callable for service_id '{service_id}': {e}")
                return None
        else:
            return type(service)

        return None

    def add_text_embedding_generation_service(
        self,
        service_id: str,
        service: Union[EmbeddingGeneratorBase, Callable[["Kernel"], EmbeddingGeneratorBase]],
        overwrite: bool = False,
    ) -> "Kernel":
        if not service_id:
            raise ValueError("service_id must be a non-empty string")
        if not overwrite and service_id in self.text_embedding_generation_services:
            raise ValueError(f"Embedding service with service_id '{service_id}' already exists")

        self.text_embedding_generation_services[service_id] = (
            service if isinstance(service, Callable) else lambda _: service
        )
        if self.default_text_embedding_generation_service is None:
            self.default_text_embedding_generation_service = service_id

        return self

    def set_default_text_completion_service(self, service_id: str) -> "Kernel":
        if service_id not in self.text_completion_services:
            raise ValueError(f"AI service with service_id '{service_id}' does not exist")

        self.default_text_completion_service = service_id
        return self

    def set_default_chat_service(self, service_id: str) -> "Kernel":
        if service_id not in self.chat_services:
            raise ValueError(f"AI service with service_id '{service_id}' does not exist")

        self.default_chat_service = service_id
        return self

    def set_default_text_embedding_generation_service(self, service_id: str) -> "Kernel":
        if service_id not in self.text_embedding_generation_services:
            raise ValueError(f"AI service with service_id '{service_id}' does not exist")

        self.default_text_embedding_generation_service = service_id
        return self

    def get_text_completion_service_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self.text_completion_services:
            if self.default_text_completion_service is None:
                raise ValueError("No default text service is set")
            return self.default_text_completion_service

        return service_id

    def get_chat_service_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self.chat_services:
            if self.default_chat_service is None:
                raise ValueError("No default chat service is set")
            return self.default_chat_service

        return service_id

    def get_text_embedding_generation_service_id(self, service_id: Optional[str] = None) -> str:
        if service_id is None or service_id not in self.text_embedding_generation_services:
            if self.default_text_embedding_generation_service is None:
                raise ValueError("No default embedding service is set")
            return self.default_text_embedding_generation_service

        return service_id

    def remove_text_completion_service(self, service_id: str) -> "Kernel":
        if service_id not in self.text_completion_services:
            raise ValueError(f"AI service with service_id '{service_id}' does not exist")

        del self.text_completion_services[service_id]
        if self.default_text_completion_service == service_id:
            self.default_text_completion_service = next(iter(self.text_completion_services), None)
        return self

    def remove_chat_service(self, service_id: str) -> "Kernel":
        if service_id not in self.chat_services:
            raise ValueError(f"AI service with service_id '{service_id}' does not exist")

        del self.chat_services[service_id]
        if self.default_chat_service == service_id:
            self.default_chat_service = next(iter(self.chat_services), None)
        return self

    def remove_text_embedding_generation_service(self, service_id: str) -> "Kernel":
        if service_id not in self.text_embedding_generation_services:
            raise ValueError(f"AI service with service_id '{service_id}' does not exist")

        del self.text_embedding_generation_services[service_id]
        if self.default_text_embedding_generation_service == service_id:
            self.default_text_embedding_generation_service = next(iter(self.text_embedding_generation_services), None)
        return self

    def clear_all_text_completion_services(self) -> "Kernel":
        self.text_completion_services = {}
        self.default_text_completion_service = None
        return self

    def clear_all_chat_services(self) -> "Kernel":
        self.chat_services = {}
        self.default_chat_service = None
        return self

    def clear_all_text_embedding_generation_services(self) -> "Kernel":
        self.text_embedding_generation_services = {}
        self.default_text_embedding_generation_service = None
        return self

    def clear_all_services(self) -> "Kernel":
        self.text_completion_services = {}
        self.chat_services = {}
        self.text_embedding_generation_services = {}

        self.default_text_completion_service = None
        self.default_chat_service = None
        self.default_text_embedding_generation_service = None

        return self

    def import_native_plugin_from_directory(self, parent_directory: str, plugin_directory_name: str) -> KernelPlugin:
        MODULE_NAME = "native_function"

        validate_plugin_name(plugin_directory_name)

        plugin_directory = os.path.abspath(os.path.join(parent_directory, plugin_directory_name))
        native_py_file_path = os.path.join(plugin_directory, f"{MODULE_NAME}.py")

        if not os.path.exists(native_py_file_path):
            raise ValueError(f"Native Plugin Python File does not exist: {native_py_file_path}")

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
            return self.import_plugin(plugin_obj, plugin_name)

        return {}

    def import_plugin_from_prompt_directory(self, parent_directory: str, plugin_directory_name: str) -> KernelPlugin:
        CONFIG_FILE = "config.json"
        PROMPT_FILE = "skprompt.txt"

        validate_plugin_name(plugin_directory_name)

        plugin_directory = os.path.join(parent_directory, plugin_directory_name)
        plugin_directory = os.path.abspath(plugin_directory)

        if not os.path.exists(plugin_directory):
            raise ValueError(f"Plugin directory does not exist: {plugin_directory_name}")

        functions = []

        directories = glob.glob(plugin_directory + "/*/")
        for directory in directories:
            dir_name = os.path.dirname(directory)
            function_name = os.path.basename(dir_name)
            prompt_path = os.path.join(directory, PROMPT_FILE)

            # Continue only if the prompt template exists
            if not os.path.exists(prompt_path):
                continue

            config_path = os.path.join(directory, CONFIG_FILE)
            with open(config_path, "r") as config_file:
                prompt_template_config = PromptTemplateConfig.from_json(config_file.read())
            prompt_template_config.name = function_name

            # Load Prompt Template
            with open(prompt_path, "r") as prompt_file:
                prompt = prompt_file.read()
                prompt_template_config.template = prompt

            kernel_prompt_template = KernelPromptTemplate(prompt_template_config)

            functions += [
                self.create_function_from_prompt(
                    prompt_template=kernel_prompt_template,
                    prompt_template_config=prompt_template_config,
                    template_format="semantic-kernel",
                    function_name=function_name,
                )
            ]

        plugin = KernelPlugin(name=plugin_directory_name, functions=functions)

        return plugin

    def add_function_invoking_handler(
        self, handler: Callable[["Kernel", FunctionInvokingEventArgs], FunctionInvokingEventArgs]
    ) -> None:
        self.function_invoking_handlers[id(handler)] = handler

    def add_function_invoked_handler(
        self, handler: Callable[["Kernel", FunctionInvokingEventArgs], FunctionInvokedEventArgs]
    ) -> None:
        self.function_invoked_handlers[id(handler)] = handler

    def remove_function_invoking_handler(self, handler: Callable) -> None:
        if id(handler) in self.function_invoking_handlers:
            del self.function_invoking_handlers[id(handler)]

    def remove_function_invoked_handler(self, handler: Callable) -> None:
        if id(handler) in self.function_invoked_handlers:
            del self.function_invoked_handlers[id(handler)]
