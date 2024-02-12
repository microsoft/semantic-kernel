# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import platform
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from pydantic import Field, StringConstraints

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.models.contents.chat_message_content import ChatMessageContent
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_handlers import DelegateHandlers
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.parameter_view import ParameterView
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext
    from semantic_kernel.plugin_definition.kernel_plugin_collection import KernelPluginCollection

# TODO: is this needed anymore after sync code removal?
if platform.system() == "Windows" and sys.version_info >= (3, 8, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger: logging.Logger = logging.getLogger(__name__)


def store_results(chat_prompt: ChatPromptTemplate, results: List["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    if hasattr(results[0], "tool_message") and results[0].tool_message is not None:
        chat_prompt.add_message(role="tool", message=results[0].tool_message)
    chat_prompt.add_message(
        "assistant",
        message=results[0].content,
        function_call=results[0].function_call if hasattr(results[0], "function_call") else None,
        tool_calls=results[0].tool_calls if hasattr(results[0], "tool_calls") else None,
    )
    return chat_prompt


class KernelFunction(KernelBaseModel):
    """
    Semantic Kernel function.

    Attributes:
        plugin_name (str): The name of the plugin that contains this function. Must be upper/lower
            case letters and underscores with a minimum length of 1.
        description (Optional[str]): The description of the function.
        name (str): The name of the function. Must be upper/lower case letters and
            underscores with a minimum length of 1.
        is_semantic (bool): Whether the function is semantic.
        stream_function (Optional[Callable[..., Any]]): The stream function for the function.
        parameters (List[ParameterView]): The parameters for the function.
        delegate_type (DelegateTypes): The delegate type for the function.
        function (Callable[..., Any]): The function to call.
        plugins (Optional[KernelPluginCollection]): The collection of plugins.
        ai_service (Optional[Union[TextCompletionClientBase, ChatCompletionClientBase]]): The AI service.
        ai_prompt_execution_settings (PromptExecutionSettings): The AI prompt execution settings.
        chat_prompt_template (Optional[ChatPromptTemplate]): The chat prompt template.
    """

    plugin_name: Annotated[str, StringConstraints(pattern=r"^[A-Za-z_]+$", min_length=1)]
    description: Optional[str] = Field(default=None)
    name: Annotated[str, StringConstraints(pattern=r"^[A-Za-z_]+$", min_length=1)]
    is_semantic: bool = Field(...)
    stream_function: Optional[Callable[..., Any]] = Field(default=None)
    parameters: List[ParameterView] = Field(...)
    delegate_type: DelegateTypes = Field(...)
    function: Callable[..., Any] = Field(...)
    plugins: Optional["KernelPluginCollection"] = Field(default=None)
    ai_service: Optional[Union[TextCompletionClientBase, ChatCompletionClientBase]] = Field(default=None)
    prompt_execution_settings: PromptExecutionSettings = Field(default_factory=PromptExecutionSettings)
    chat_prompt_template: Optional[ChatPromptTemplate] = Field(default=None)

    def __init__(
        self,
        delegate_type: DelegateTypes,
        delegate_function: Callable[..., Any],
        parameters: List[ParameterView],
        description: str,
        plugin_name: str,
        function_name: str,
        is_semantic: bool,
        delegate_stream_function: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initializes a new instance of the KernelFunction class

        Args:
            delegate_type (DelegateTypes): The delegate type for the function
            delegate_function (Callable[..., Any]): The delegate function for the function
            parameters (List[ParameterView]): The parameters for the function
            description (str): The description for the function
            plugin_name (str): The name of the plugin
            name (str): The name of the function
            is_semantic (bool): Whether the function is semantic
            delegate_stream_function (Optional[Callable[..., Any]]): The delegate stream function for the function
            kwargs (Dict[str, Any]): Additional keyword arguments
        """
        chat_prompt_template = kwargs.pop("chat_prompt_template", None)

        super().__init__(
            delegate_type=delegate_type,
            function=delegate_function,
            parameters=parameters,
            description=description,
            plugin_name=plugin_name,
            name=function_name,
            is_semantic=is_semantic,
            stream_function=delegate_stream_function,
            chat_prompt_template=chat_prompt_template,
            **kwargs,
        )

    @staticmethod
    def from_native_method(method: Callable[..., Any], plugin_name: str) -> "KernelFunction":
        """
        Create a KernelFunction from a native method.

        Args:
            method (Callable[..., Any]): The method to create the function from
            plugin_name (str): The name of the plugin

        Returns:
            KernelFunction: The kernel function
        """
        if method is None:
            raise ValueError("Method cannot be `None`")

        assert method.__kernel_function__ is not None, "Method is not a Kernel function"
        assert method.__kernel_function_name__ is not None, "Method name is empty"

        parameters = []
        # kernel_function_context_parameters are optionals
        if hasattr(method, "__kernel_function_context_parameters__"):
            for param in method.__kernel_function_context_parameters__:
                assert "name" in param, "Parameter name is empty"
                assert "description" in param, "Parameter description is empty"
                assert "default_value" in param, "Parameter default value is empty"

                parameters.append(
                    ParameterView(
                        name=param["name"],
                        description=param["description"],
                        default_value=param["default_value"],
                        type=param.get("type", "string"),
                        required=param.get("required", False),
                    )
                )

        if (
            hasattr(method, "__kernel_function_input_description__")
            and method.__kernel_function_input_description__ is not None
            and method.__kernel_function_input_description__ != ""
        ):
            input_param = ParameterView(
                name="input",
                description=method.__kernel_function_input_description__,
                default_value=method.__kernel_function_input_default_value__,
                type="string",
                required=False,
            )
            parameters = [input_param] + parameters

        return KernelFunction(
            delegate_type=DelegateInference.infer_delegate_type(method),
            delegate_function=method,
            delegate_stream_function=method,
            parameters=parameters,
            description=method.__kernel_function_description__,
            plugin_name=plugin_name,
            function_name=method.__kernel_function_name__,
            is_semantic=False,
        )

    @staticmethod
    def from_semantic_config(
        plugin_name: str,
        function_name: str,
        function_config: SemanticFunctionConfig,
    ) -> "KernelFunction":
        """
        Create a KernelFunction from a semantic configuration.

        Args:
            plugin_name (str): The name of the plugin
            function_name (str): The name of the function
            function_config (SemanticFunctionConfig): The function configuration

        Returns:
            KernelFunction: The kernel function
        """
        if function_config is None:
            raise ValueError("Function configuration cannot be `None`")

        async def _local_func(client, prompt_execution_settings, context: "KernelContext", **kwargs):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            if not function_config.has_chat_prompt:
                try:
                    prompt = await function_config.prompt_template.render(context)
                    results = await client.complete(prompt, prompt_execution_settings)
                    context.objects["results"] = results
                    context.variables.update(str(results[0]))
                except Exception as e:
                    # TODO: "critical exceptions"
                    context.fail(str(e), e)
                finally:
                    return context

            try:
                chat_prompt = function_config.prompt_template
                # Similar to non-chat, render prompt (which renders to a
                # dict of <role, content, name> messages)
                messages = await chat_prompt.render_messages(context)
                results = await client.complete_chat(messages, prompt_execution_settings)
                context.objects["results"] = results
                if results[0].content is not None:
                    context.variables.update(str(results[0]))
                # TODO: most of this will be deleted once context is gone, just AIResponse object is then returned.
                chat_prompt = store_results(chat_prompt, results)
            except Exception as exc:
                # TODO: "critical exceptions"
                context.fail(str(exc), exc)
            finally:
                return context

        async def _local_stream_func(client, prompt_execution_settings, context):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            if not function_config.has_chat_prompt:
                try:
                    prompt = await function_config.prompt_template.render(context)
                    result = client.complete_stream(prompt, prompt_execution_settings)
                    async for chunk in result:
                        yield chunk
                except Exception as e:
                    # TODO: "critical exceptions"
                    context.fail(str(e), e)
                return

            try:
                chat_prompt = function_config.prompt_template
                # Similar to non-chat, render prompt (which renders to a
                # list of <role, content> messages)
                messages = await chat_prompt.render_messages(context)
                result = client.complete_chat_stream(messages=messages, settings=prompt_execution_settings)
                # context.objects["response_object"] = result
                # TODO: most of this will be deleted once context is gone, just AIResponse object is then returned.
                async for chunk in result:
                    yield chunk
                # context, chat_prompt = store_results(context, result, chat_prompt)
            except Exception as e:
                # TODO: "critical exceptions"
                logger.error(f"Error occurred while invoking stream function: {str(e)}")
                context.fail(str(e), e)

        return KernelFunction(
            delegate_type=DelegateTypes.ContextSwitchInKernelContextOutTaskKernelContext,
            delegate_function=_local_func,
            delegate_stream_function=_local_stream_func,
            parameters=function_config.prompt_template.get_parameters(),
            description=function_config.prompt_template_config.description,
            plugin_name=plugin_name,
            function_name=function_name,
            is_semantic=True,
            chat_prompt_template=function_config.prompt_template if function_config.has_chat_prompt else None,
        )

    def set_default_plugin_collection(self, plugins: "KernelPluginCollection") -> "KernelFunction":
        self.plugins = plugins
        return self

    def set_ai_service(self, ai_service: Callable[[], TextCompletionClientBase]) -> "KernelFunction":
        if ai_service is None:
            raise ValueError("AI LLM service factory cannot be `None`")
        self._verify_is_semantic()
        self.ai_service = ai_service()
        return self

    def set_chat_service(self, chat_service: Callable[[], ChatCompletionClientBase]) -> "KernelFunction":
        if chat_service is None:
            raise ValueError("Chat LLM service factory cannot be `None`")
        self._verify_is_semantic()
        self.ai_service = chat_service()
        return self

    def set_ai_configuration(self, settings: PromptExecutionSettings) -> "KernelFunction":
        if settings is None:
            raise ValueError("AI LLM request settings cannot be `None`")
        self._verify_is_semantic()
        self.prompt_execution_settings = settings
        return self

    def set_chat_configuration(self, settings: PromptExecutionSettings) -> "KernelFunction":
        if settings is None:
            raise ValueError("Chat LLM request settings cannot be `None`")
        self._verify_is_semantic()
        self.prompt_execution_settings = settings
        return self

    def describe(self) -> FunctionView:
        return FunctionView(
            name=self.name,
            plugin_name=self.plugin_name,
            description=self.description,
            is_semantic=self.is_semantic,
            parameters=self.parameters,
        )

    async def __call__(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["KernelContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[PromptExecutionSettings] = None,
        log: Optional[Any] = None,
    ) -> "KernelContext":
        """
        Override the call operator to allow calling the function directly
        This operator is run asynchronously.

        Arguments:
            input {Optional[str]} -- The input to the function
            variables {ContextVariables} -- The variables for the function
            context {Optional[KernelContext]} -- The context for the function
            memory {Optional[SemanticTextMemoryBase]} -- The memory for the function
            settings {Optional[PromptExecutionSettings]} -- The settings for the function
            log {Optional[Any]} -- A logger to use for logging. (Optional)

        Returns:
            KernelContext -- The context for the function

        Raises:
            KernelException -- If the function is not semantic
        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        return await self.invoke(
            input=input,
            variables=variables,
            context=context,
            memory=memory,
            settings=settings,
        )

    async def invoke(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["KernelContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[PromptExecutionSettings] = None,
        **kwargs: Dict[str, Any],
    ) -> "KernelContext":
        """
        Invoke the function asynchronously

        Arguments:
            input {Optional[str]} -- The input to the function
            variables {ContextVariables} -- The variables for the function
            context {Optional[KernelContext]} -- The context for the function
            memory {Optional[SemanticTextMemoryBase]} -- The memory for the function
            settings {Optional[PromptExecutionSettings]} -- The settings for the function
            kwargs {Dict[str, Any]} -- Additional keyword arguments

        Returns:
            KernelContext -- The context for the function

        Raises:
            KernelException -- If there is a problem invoking the function
        """
        from semantic_kernel.orchestration.kernel_context import KernelContext

        if context is None:
            context = KernelContext(
                variables=ContextVariables("") if variables is None else variables,
                memory=memory if memory is not None else NullMemory.instance,
                plugins=self.plugins,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
            if memory is not None:
                context.memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            if self.is_semantic:
                return await self._invoke_semantic(context, settings, **kwargs)
            else:
                return await self._invoke_native(context, **kwargs)
        except Exception as e:
            context.fail(str(e), e)
            return context

    async def _invoke_semantic(self, context: "KernelContext", settings: PromptExecutionSettings, **kwargs):
        self._verify_is_semantic()
        self._ensure_context_has_plugins(context)
        new_context = await self.function(self.ai_service, settings or self.prompt_execution_settings, context)
        context.variables.merge_or_overwrite(new_context.variables)
        return context

    async def _invoke_native(self, context):
        self._verify_is_native()

        self._ensure_context_has_plugins(context)

        delegate = DelegateHandlers.get_handler(self.delegate_type)
        # for python3.9 compatibility (staticmethod is not callable)
        if not hasattr(delegate, "__call__"):
            delegate = delegate.__func__
        new_context = await delegate(self.function, context)

        return new_context

    def _verify_is_semantic(self) -> None:
        if self.is_semantic:
            return

        logger.error("The function is not semantic")
        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a semantic function",
        )

    def _verify_is_native(self) -> None:
        if not self.is_semantic:
            return

        logger.error("The function is not native")
        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a native function",
        )

    async def invoke_stream(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["KernelContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[PromptExecutionSettings] = None,
    ):
        from semantic_kernel.orchestration.kernel_context import KernelContext

        if context is None:
            context = KernelContext(
                variables=ContextVariables("") if variables is None else variables,
                memory=memory if memory is not None else NullMemory.instance,
                plugins=self.plugins,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
            if memory is not None:
                context._memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            if self.is_semantic:
                async for stream_msg in self._invoke_semantic_stream(context, settings):
                    yield stream_msg
            else:
                async for stream_msg in self._invoke_native_stream(context):
                    yield stream_msg
        except Exception as e:
            logger.error(f"Error occurred while invoking stream function: {str(e)}")
            context.fail(str(e), e)
            raise KernelException(
                KernelException.ErrorCodes.FunctionInvokeError,
                "Error occurred while invoking stream function",
            )

    async def _invoke_semantic_stream(self, context, settings):
        self._verify_is_semantic()
        self._ensure_context_has_plugins(context)
        async for stream_msg in self.stream_function(
            self.ai_service, settings or self.prompt_execution_settings, context
        ):
            yield stream_msg

    async def _invoke_native_stream(self, context):
        self._verify_is_native()

        self._ensure_context_has_plugins(context)

        delegate = DelegateHandlers.get_handler(self._delegate_type)
        # for python3.9 compatibility (staticmethod is not callable)
        if not hasattr(delegate, "__call__"):
            delegate = delegate.__func__

        completion = ""
        async for partial in delegate(self.function, context):
            completion += partial
            yield partial

        context.variables.update(completion)

    def _ensure_context_has_plugins(self, context) -> None:
        if context.plugins is not None:
            return

        context.plugins = self.plugins

    def _trace_function_type_Call(self, type: Enum) -> None:
        logger.debug(f"Executing function type {type}: {type.name}")
