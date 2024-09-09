# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator, AsyncIterable, Callable
from copy import copy
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.const import METADATA_EXCEPTION_KEY
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.exceptions import (
    FunctionCallInvalidArgumentsException,
    FunctionExecutionException,
    KernelFunctionNotFoundError,
    KernelInvokeException,
    OperationCancelledException,
    TemplateSyntaxError,
)
from semantic_kernel.exceptions.kernel_exceptions import KernelServiceNotFoundError
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.kernel_filters_extension import (
    KernelFilterExtension,
    _rebuild_auto_function_invocation_context,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_extension import KernelFunctionExtension
from semantic_kernel.functions.kernel_function_from_prompt import (
    KernelFunctionFromPrompt,
)
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_types import AI_SERVICE_CLIENT_TYPE, OneOrMany
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME
from semantic_kernel.reliability.kernel_reliability_extension import (
    KernelReliabilityExtension,
)
from semantic_kernel.services.ai_service_selector import AIServiceSelector
from semantic_kernel.services.kernel_services_extension import KernelServicesExtension
from semantic_kernel.utils.naming import generate_random_ascii_name

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionChoiceBehavior,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.functions.kernel_function import KernelFunction

T = TypeVar("T")

TDataModel = TypeVar("TDataModel")

logger: logging.Logger = logging.getLogger(__name__)


class Kernel(
    KernelFilterExtension,
    KernelFunctionExtension,
    KernelServicesExtension,
    KernelReliabilityExtension,
):
    """The Kernel of Semantic Kernel.

    This is the main entry point for Semantic Kernel. It provides the ability to run
    functions and manage filters, plugins, and AI services.

    Attributes:
        function_invocation_filters: Filters applied during function invocation, from KernelFilterExtension.
        prompt_rendering_filters: Filters applied during prompt rendering, from KernelFilterExtension.
        auto_function_invocation_filters: Filters applied during auto function invocation, from KernelFilterExtension.
        plugins: A dict with the plugins registered with the Kernel, from KernelFunctionExtension.
        services: A dict with the services registered with the Kernel, from KernelServicesExtension.
        ai_service_selector: The AI service selector to be used by the kernel, from KernelServicesExtension.
        retry_mechanism: The retry mechanism to be used by the kernel, from KernelReliabilityExtension.

    """

    def __init__(
        self,
        plugins: (
            KernelPlugin | dict[str, KernelPlugin] | list[KernelPlugin] | None
        ) = None,
        services: (
            AI_SERVICE_CLIENT_TYPE
            | list[AI_SERVICE_CLIENT_TYPE]
            | dict[str, AI_SERVICE_CLIENT_TYPE]
            | None
        ) = None,
        ai_service_selector: AIServiceSelector | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new instance of the Kernel class.

        Args:
            plugins: The plugins to be used by the kernel, will be rewritten to a dict with plugin name as key
            services: The services to be used by the kernel, will be rewritten to a dict with service_id as key
            ai_service_selector: The AI service selector to be used by the kernel,
                default is based on order of execution settings.
            **kwargs: Additional fields to be passed to the Kernel model,
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

    async def invoke_stream(
        self,
        function: "KernelFunction | None" = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        metadata: dict[str, Any] = {},
        return_function_results: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[
        list["StreamingContentMixin"] | FunctionResult | list[FunctionResult], Any
    ]:
        """Execute one or more stream functions.

        This will execute the functions in the order they are provided, if a list of functions is provided.
        When multiple functions are provided only the last one is streamed, the rest is executed as a pipeline.

        Args:
            function (KernelFunction): The function to execute,
                this value has precedence when supplying both this and using function_name and plugin_name,
                if this is none, function_name and plugin_name are used and cannot be None.
            arguments (KernelArguments | None): The arguments to pass to the function(s), optional
            function_name (str | None): The name of the function to execute
            plugin_name (str | None): The name of the plugin to execute
            metadata (dict[str, Any]): The metadata to pass to the function(s)
            return_function_results (bool): If True, the function results are yielded as a list[FunctionResult]
            in addition to the streaming content, otherwise only the streaming content is yielded.
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Yields:
            StreamingContentMixin: The content of the stream of the last function provided.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)
        if not function:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError(
                    "No function(s) or function- and plugin-name provided"
                )
            function = self.get_function(plugin_name, function_name)

        function_result: list[list["StreamingContentMixin"] | Any] = []

        async for stream_message in function.invoke_stream(self, arguments):
            if isinstance(stream_message, FunctionResult) and (
                exception := stream_message.metadata.get(METADATA_EXCEPTION_KEY, None)
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
            yield FunctionResult(
                function=function.metadata, value=output_function_result
            )

    async def invoke(
        self,
        function: "KernelFunction | None" = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> FunctionResult | None:
        """Execute a function and return the FunctionResult.

        Args:
            function (KernelFunction): The function or functions to execute,
                this value has precedence when supplying both this and using function_name and plugin_name,
                if this is none, function_name and plugin_name are used and cannot be None.
            arguments (KernelArguments): The arguments to pass to the function(s), optional
            function_name (str | None): The name of the function to execute
            plugin_name (str | None): The name of the plugin to execute
            metadata (dict[str, Any]): The metadata to pass to the function(s)
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Raises:
            KernelInvokeException: If an error occurs during function invocation

        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)
        if not function:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError(
                    "No function, or function name and plugin name provided"
                )
            function = self.get_function(plugin_name, function_name)

        try:
            return await function.invoke(
                kernel=self, arguments=arguments, metadata=metadata
            )
        except OperationCancelledException as exc:
            logger.info(
                f"Operation cancelled during function invocation. Message: {exc}"
            )
            return None
        except Exception as exc:
            logger.error(
                "Something went wrong in function invocation. During function invocation:"
                f" '{function.fully_qualified_name}'. Error description: '{exc!s}'"
            )
            raise KernelInvokeException(
                f"Error occurred while invoking function: '{function.fully_qualified_name}'"
            ) from exc

    async def invoke_prompt(
        self,
        prompt: str,
        function_name: str | None = None,
        plugin_name: str | None = None,
        arguments: KernelArguments | None = None,
        template_format: Literal[
            "semantic-kernel",
            "handlebars",
            "jinja2",
        ] = KERNEL_TEMPLATE_FORMAT_NAME,
        **kwargs: Any,
    ) -> FunctionResult | None:
        """Invoke a function from the provided prompt.

        Args:
            prompt (str): The prompt to use
            function_name (str): The name of the function, optional
            plugin_name (str): The name of the plugin, optional
            arguments (KernelArguments | None): The arguments to pass to the function(s), optional
            template_format (str | None): The format of the prompt template
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Returns:
            FunctionResult | list[FunctionResult] | None: The result of the function(s)
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        if not prompt:
            raise TemplateSyntaxError("The prompt is either null or empty.")

        function = KernelFunctionFromPrompt(
            function_name=function_name or generate_random_ascii_name(),
            plugin_name=plugin_name,
            prompt=prompt,
            template_format=template_format,
        )
        return await self.invoke(function=function, arguments=arguments)

    async def invoke_prompt_stream(
        self,
        prompt: str,
        function_name: str | None = None,
        plugin_name: str | None = None,
        arguments: KernelArguments | None = None,
        template_format: Literal[
            "semantic-kernel",
            "handlebars",
            "jinja2",
        ] = KERNEL_TEMPLATE_FORMAT_NAME,
        return_function_results: bool | None = False,
        **kwargs: Any,
    ) -> AsyncIterable[
        list["StreamingContentMixin"] | FunctionResult | list[FunctionResult]
    ]:
        """Invoke a function from the provided prompt and stream the results.

        Args:
            prompt (str): The prompt to use
            function_name (str): The name of the function, optional
            plugin_name (str): The name of the plugin, optional
            arguments (KernelArguments | None): The arguments to pass to the function(s), optional
            template_format (str | None): The format of the prompt template
            return_function_results (bool): If True, the function results are yielded as a list[FunctionResult]
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Returns:
            AsyncIterable[StreamingContentMixin]: The content of the stream of the last function provided.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        if not prompt:
            raise TemplateSyntaxError("The prompt is either null or empty.")

        from semantic_kernel.functions.kernel_function_from_prompt import (
            KernelFunctionFromPrompt,
        )

        function = KernelFunctionFromPrompt(
            function_name=function_name or generate_random_ascii_name(),
            plugin_name=plugin_name,
            prompt=prompt,
            template_format=template_format,
        )

        function_result: list[list["StreamingContentMixin"] | Any] = []

        async for stream_message in self.invoke_stream(
            function=function, arguments=arguments
        ):
            if isinstance(stream_message, FunctionResult) and (
                exception := stream_message.metadata.get(METADATA_EXCEPTION_KEY, None)
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
            yield FunctionResult(
                function=function.metadata, value=output_function_result
            )

    async def invoke_function_call(
        self,
        function_call: FunctionCallContent,
        chat_history: ChatHistory,
        arguments: "KernelArguments | None" = None,
        function_call_count: int | None = None,
        request_index: int | None = None,
        function_behavior: "FunctionChoiceBehavior" = None,  # type: ignore
    ) -> "AutoFunctionInvocationContext | None":
        """Processes the provided FunctionCallContent and updates the chat history."""
        args_cloned = copy(arguments) if arguments else KernelArguments()
        try:
            parsed_args = function_call.to_kernel_arguments()
            if parsed_args:
                args_cloned.update(parsed_args)
        except (FunctionCallInvalidArgumentsException, TypeError) as exc:
            logger.info(
                f"Received invalid arguments for function {function_call.name}: {exc}. Trying tool call again."
            )
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call,
                result="The tool call arguments are malformed. Arguments must be in JSON format. Please try again.",
            )
            chat_history.add_message(message=frc.to_chat_message_content())
            return None

        try:
            if function_call.name is None:
                raise FunctionExecutionException("The function name is required.")
            if function_behavior is not None and function_behavior.filters:
                allowed_functions = [
                    func.fully_qualified_name
                    for func in self.get_list_of_function_metadata(
                        function_behavior.filters
                    )
                ]
                if function_call.name not in allowed_functions:
                    raise FunctionExecutionException(
                        f"Only functions: {allowed_functions} are allowed, {function_call.name} is not allowed."
                    )
            function_to_call = self.get_function(
                function_call.plugin_name, function_call.function_name
            )
        except Exception as exc:
            logger.exception(
                f"The function `{function_call.name}` is not part of the provided functions: {exc}."
            )
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call,
                result=(
                    f"The tool call with name `{function_call.name}` is not part of the provided tools, "
                    "please try again with a supplied tool call name and make sure to validate the name."
                ),
            )
            chat_history.add_message(message=frc.to_chat_message_content())
            return None

        num_required_func_params = len(
            [param for param in function_to_call.parameters if param.is_required]
        )
        if parsed_args is None or len(parsed_args) < num_required_func_params:
            msg = (
                f"There are `{num_required_func_params}` tool call arguments required and "
                f"only `{len(parsed_args) if parsed_args is not None else 0}` received. The required arguments are: "
                f"{[param.name for param in function_to_call.parameters if param.is_required]}. "
                "Please provide the required arguments and try again."
            )
            logger.info(msg)
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call,
                result=msg,
            )
            chat_history.add_message(message=frc.to_chat_message_content())
            return None

        logger.info(
            f"Calling {function_call.name} function with args: {function_call.arguments}"
        )

        _rebuild_auto_function_invocation_context()
        invocation_context = AutoFunctionInvocationContext(
            function=function_to_call,
            kernel=self,
            arguments=args_cloned,
            chat_history=chat_history,
            function_result=FunctionResult(
                function=function_to_call.metadata, value=None
            ),
            function_count=function_call_count or 0,
            request_sequence_index=request_index or 0,
        )
        if function_call.index is not None:
            invocation_context.function_sequence_index = function_call.index

        stack = self.construct_call_stack(
            filter_type=FilterTypes.AUTO_FUNCTION_INVOCATION,
            inner_function=self._inner_auto_function_invoke_handler,
        )
        await stack(invocation_context)

        frc = FunctionResultContent.from_function_call_content_and_result(
            function_call_content=function_call,
            result=invocation_context.function_result,
        )
        chat_history.add_message(message=frc.to_chat_message_content())

        return invocation_context if invocation_context.terminate else None

    async def _inner_auto_function_invoke_handler(
        self, context: AutoFunctionInvocationContext
    ):
        """Inner auto function invocation handler."""
        try:
            result = await context.function.invoke(context.kernel, context.arguments)
            if result:
                context.function_result = result
        except Exception as exc:
            logger.exception(
                f"Error invoking function {context.function.fully_qualified_name}: {exc}."
            )
            value = f"An error occurred while invoking the function {context.function.fully_qualified_name}: {exc}"
            if context.function_result is not None:
                context.function_result.value = value
            else:
                context.function_result = FunctionResult(
                    function=context.function.metadata, value=value
                )
            return

    async def add_embedding_to_object(
        self,
        inputs: OneOrMany[TDataModel],
        field_to_embed: str,
        field_to_store: str,
        execution_settings: dict[str, "PromptExecutionSettings"],
        container_mode: bool = False,
        cast_function: Callable[[list[float]], Any] | None = None,
        **kwargs: Any,
    ):
        """Gather all fields to embed, batch the embedding generation and store."""
        contents: list[Any] = []
        dict_like = (getter := getattr(inputs, "get", False)) and callable(getter)
        list_of_dicts: bool = False
        if container_mode:
            contents = inputs[field_to_embed].tolist()  # type: ignore
        elif isinstance(inputs, list):
            list_of_dicts = (getter := getattr(inputs[0], "get", False)) and callable(
                getter
            )
            for record in inputs:
                if list_of_dicts:
                    contents.append(record.get(field_to_embed))  # type: ignore
                else:
                    contents.append(getattr(record, field_to_embed))
        else:
            if dict_like:
                contents.append(inputs.get(field_to_embed))  # type: ignore
            else:
                contents.append(getattr(inputs, field_to_embed))
        vectors = None
        service: EmbeddingGeneratorBase | None = None
        for service_id, settings in execution_settings.items():
            service = self.get_service(service_id, type=EmbeddingGeneratorBase)  # type: ignore
            if service:
                vectors = await service.generate_raw_embeddings(texts=contents, settings=settings, **kwargs)  # type: ignore
                break
        if not service:
            raise KernelServiceNotFoundError("No service found to generate embeddings.")
        if vectors is None:
            raise KernelInvokeException("No vectors were generated.")
        if cast_function:
            vectors = [cast_function(vector) for vector in vectors]
        if container_mode:
            inputs[field_to_store] = vectors  # type: ignore
            return
        if isinstance(inputs, list):
            for record, vector in zip(inputs, vectors):
                if list_of_dicts:
                    record[field_to_store] = vector  # type: ignore
                else:
                    setattr(record, field_to_store, vector)
            return
        if dict_like:
            inputs[field_to_store] = vectors[0]  # type: ignore
            return
        setattr(inputs, field_to_store, vectors[0])
from logging import Logger
from typing import Any, Dict, Optional

from semantic_kernel.ai.ai_exception import AIException
from semantic_kernel.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)
from semantic_kernel.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)
from semantic_kernel.configuration.backend_types import BackendType
from semantic_kernel.configuration.kernel_config import KernelConfig
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.skill_definition.skill_collection import SkillCollection
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase
from semantic_kernel.template_engine.prompt_template_engine_base import (
    PromptTemplateEngineBase,
)


class Kernel(KernelBase):
    _log: Logger
    _config: KernelConfig
    _skill_collection: SkillCollectionBase
    _prompt_template_engine: PromptTemplateEngineBase
    _memory: SemanticTextMemoryBase

    def __init__(
        self,
        skill_collection: SkillCollectionBase,
        prompt_template_engine: PromptTemplateEngineBase,
        memory: SemanticTextMemoryBase,
        config: KernelConfig,
        log: Logger,
    ) -> None:
        self._log = log
        self._config = config
        self._skill_collection = skill_collection
        self._prompt_template_engine = prompt_template_engine
        self._memory = memory

    @property
    def config(self) -> KernelConfig:
        return self._config

    @property
    def logger(self) -> Logger:
        return self._log

    @property
    def memory(self) -> SemanticTextMemoryBase:
        return self._memory

    @property
    def prompt_template_engine(self) -> PromptTemplateEngineBase:
        return self._prompt_template_engine

    @property
    def skills(self) -> ReadOnlySkillCollectionBase:
        return self._skill_collection.read_only_skill_collection

    def register_semantic_function(
        self,
        skill_name: Optional[str],
        function_name: str,
        function_config: SemanticFunctionConfig,
    ) -> SKFunctionBase:
        if skill_name is None or skill_name == "":
            skill_name = SkillCollection.GLOBAL_SKILL
        assert skill_name is not None  # for type checker

        Verify.valid_skill_name(skill_name)
        Verify.valid_function_name(function_name)

        function = self._create_semantic_function(
            skill_name, function_name, function_config
        )
        self._skill_collection.add_semantic_function(function)

        return function

    async def run_async(self, *functions: Any) -> SKContext:
        return await self.run_on_vars_async(ContextVariables(), *functions)

    async def run_on_str_async(self, input_str: str, *functions: Any) -> SKContext:
        return await self.run_on_vars_async(ContextVariables(input_str), *functions)

    async def run_on_vars_async(
        self, input_vars: ContextVariables, *functions: Any
    ) -> SKContext:
        context = SKContext(
            input_vars,
            self._memory,
            self._skill_collection.read_only_skill_collection,
            self._log,
        )

        pipeline_step = 0
        for func in functions:
            assert isinstance(func, SKFunctionBase), (
                "All func arguments to Kernel.run*(inputs, func1, func2, ...) "
                "must be SKFunctionBase instances"
            )

            if context.error_occurred:
                self._log.error(
                    f"Something went wrong in pipeline step {pipeline_step}. "
                    f"Error description: '{context.last_error_description}'"
                )
                return context

            pipeline_step += 1

            try:
                context = await func.invoke_async(input=None, context=context)

                if context.error_occurred:
                    self._log.error(
                        f"Something went wrong in pipeline step {pipeline_step}. "
                        f"During function invocation: '{func.skill_name}.{func.name}'. "
                        f"Error description: '{context.last_error_description}'"
                    )
                    return context
            except Exception as ex:
                self._log.error(
                    f"Something went wrong in pipeline step {pipeline_step}. "
                    f"During function invocation: '{func.skill_name}.{func.name}'. "
                    f"Error description: '{str(ex)}'"
                )
                context.fail(str(ex), ex)
                return context

        return context

    def func(self, skill_name: str, function_name: str) -> SKFunctionBase:
        if self.skills.has_native_function(skill_name, function_name):
            return self.skills.get_native_function(skill_name, function_name)

        return self.skills.get_semantic_function(skill_name, function_name)

    def register_memory(self, memory: SemanticTextMemoryBase) -> None:
        self._memory = memory

    def create_new_context(self) -> SKContext:
        return SKContext(
            ContextVariables(),
            self._memory,
            self.skills,
            self._log,
        )

    def import_skill(
        self, skill_instance: Any, skill_name: str = ""
    ) -> Dict[str, SKFunctionBase]:
        if skill_name.strip() == "":
            skill_name = SkillCollection.GLOBAL_SKILL
            self._log.debug(f"Importing skill {skill_name} into the global namespace")
        else:
            self._log.debug(f"Importing skill {skill_name}")

        functions = []
        # Read every method from the skill instance
        for candidate in skill_instance.__dict__.values():
            # We're looking for a @staticmethod
            if not isinstance(candidate, staticmethod):
                continue
            candidate = candidate.__func__

            # If the method is a semantic function, register it
            if hasattr(candidate, "__sk_function_name__"):
                functions.append(
                    SKFunction.from_native_method(candidate, skill_name, self.logger)
                )

        self.logger.debug(f"Methods imported: {len(functions)}")

        # Uniqueness check on function names
        function_names = [f.name for f in functions]
        if len(function_names) != len(set(function_names)):
            raise KernelException(
                KernelException.ErrorCodes.FunctionOverloadNotSupported,
                "Overloaded functions are not supported, "
                "please differentiate function names.",
            )

        skill = {}
        for function in functions:
            function.set_default_skill_collection(self.skills)
            self._skill_collection.add_native_function(function)
            skill[function.name] = function

        return skill

    def _create_semantic_function(
        self,
        skill_name: str,
        function_name: str,
        function_config: SemanticFunctionConfig,
    ) -> SKFunctionBase:
        function_type = function_config.prompt_template_config.type
        if not function_type == "completion":
            raise AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                f"Function type not supported: {function_type}",
            )

        function = SKFunction.from_semantic_config(
            skill_name, function_name, function_config
        )
        function.request_settings.update_from_completion_config(
            function_config.prompt_template_config.completion
        )

        # Connect the function to the current kernel skill
        # collection, in case the function is invoked manually
        # without a context and without a way to find other functions.
        function.set_default_skill_collection(self.skills)

        # TODO: allow to postpone this (use lazy init)
        # allow to create semantic functions without
        # a default backend
        backend = self._config.get_completion_backend(
            function_config.prompt_template_config.default_backends[0]
            if len(function_config.prompt_template_config.default_backends) > 0
            else None
        )

        function.set_ai_configuration(
            CompleteRequestSettings.from_completion_config(
                function_config.prompt_template_config.completion
            )
        )

        if backend.backend_type == BackendType.AzureOpenAI:
            Verify.not_null(
                backend.azure_open_ai, "Azure OpenAI configuration is missing"
            )
            function.set_ai_backend(
                lambda: AzureTextCompletion(
                    backend.azure_open_ai.deployment_name,  # type: ignore
                    backend.azure_open_ai.endpoint,  # type: ignore
                    backend.azure_open_ai.api_key,  # type: ignore
                    backend.azure_open_ai.api_version,  # type: ignore
                    self._log,
                )
            )
        elif backend.backend_type == BackendType.OpenAI:
            Verify.not_null(backend.open_ai, "OpenAI configuration is missing")
            function.set_ai_backend(
                lambda: OpenAITextCompletion(
                    backend.open_ai.model_id,  # type: ignore
                    backend.open_ai.api_key,  # type: ignore
                    backend.open_ai.org_id,  # type: ignore
                    self._log,
                )
            )
        else:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                f"Unknown/unsupported backend type: {backend.backend_type.name}, "
                f"unable to prepare semantic function. Function description: "
                f"{function_config.prompt_template_config.description}",
            )

        return function
