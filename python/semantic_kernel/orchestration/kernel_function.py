# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import platform
import sys
from enum import Enum
from typing import TYPE_CHECKING, Any, AsyncIterable, Callable, Dict, List, Optional, Union

from pydantic import Field, StringConstraints

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.models.contents.chat_message_content import ChatMessageContent
from semantic_kernel.models.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.orchestration.function_result import FunctionResult
from semantic_kernel.orchestration.kernel_arguments import KernelArguments
from semantic_kernel.plugin_definition.function_view import FunctionView
from semantic_kernel.plugin_definition.parameter_view import ParameterView
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
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

        if not hasattr(method, "__kernel_function__") or method.__kernel_function__ is None:
            raise ValueError("Method is not a Kernel function")

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

        async def _local_func(
            self,
            client: Union[TextCompletionClientBase, ChatCompletionClientBase],
            request_settings: PromptExecutionSettings,
            arguments: KernelArguments,
        ) -> "FunctionResult":
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")
            try:
                if not function_config.has_chat_prompt:
                    prompt = await function_config.prompt_template.render(arguments)
                    completion = await client.complete(prompt, request_settings)
                    return FunctionResult(function=self, value=completion)
            except Exception as e:
                logger.error(f"Error occurred while invoking function {self.function.name}: {e}")
                raise e

            messages = await function_config.prompt_template.render_messages(arguments)
            try:
                result = await client.complete_chat(messages, request_settings)
                return FunctionResult(function=self, value=result)
            except Exception as exc:
                logger.error(f"Error occurred while invoking function {self.function.name}: {exc}")
                raise exc

        async def _local_stream_func(
            self, client: AIServiceClientBase, request_settings: PromptExecutionSettings, **kwargs
        ):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            try:
                if function_config.has_chat_prompt:
                    messages = await function_config.prompt_template.render_messages(**kwargs)
                    async for partial_content in client.complete_chat_stream(
                        messages=messages, settings=request_settings
                    ):
                        yield partial_content
                else:
                    prompt = await function_config.prompt_template.render(**kwargs)
                    async for partial_content in client.complete_stream(prompt, request_settings):
                        yield partial_content

            except Exception as e:
                logger.error(f"Error occurred while invoking function {self.function.name}: {e}")
                raise e

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
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        return await self.invoke(kernel, arguments)

    # def invoke(
    #     self,
    #     settings: Optional[AIRequestSettings] = None,
    #     **kwargs: Dict[str, Any],
    # ) -> "FunctionResult":
    #     # if context is None:
    #     #     context = KernelContext(
    #     #         variables=ContextVariables("") if variables is None else variables,
    #     #         plugin_collection=self._plugin_collection,
    #     #         memory=memory if memory is not None else NullMemory.instance,
    #     #     )
    #     # else:
    #     #     # If context is passed, we need to merge the variables
    #     #     if variables is not None:
    #     #         context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
    #     #     if memory is not None:
    #     #         context.memory = memory

    #     # if input is not None:
    #     #     context.variables.update(input)

    #     try:
    #         loop = asyncio.get_running_loop() if asyncio.get_event_loop().is_running() else None
    #     except RuntimeError:
    #         loop = None

    #     if loop and loop.is_running():

    #         def run_coroutine():
    #             if self.is_semantic:
    #                 return self._invoke_semantic(context, settings)
    #             else:
    #                 return self._invoke_native(context)

    #         return self.run_async_in_executor(run_coroutine)
    #     else:
    #         if self.is_semantic:
    #             return asyncio.run(self._invoke_semantic(context, settings))
    #         else:
    #             return asyncio.run(self._invoke_native(context))

    async def invoke(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        return await self._function(kernel, self._ai_service, arguments.execution_settings[self._ai_service], arguments)
        # try:
        #     if self.is_semantic:
        #         return await self._invoke_semantic(settings, **kwargs)
        #     else:
        #         return await self._invoke_native(settings, **kwargs)
        # except Exception as e:
        #     logger.error(f"Error occurred while invoking function {self.name}: {e}")
        #     raise e

    # async def _invoke_semantic(self, settings: AIRequestSettings, **kwargs) -> FunctionResult:
    #     self._verify_is_semantic()
    #     return await self._function(self._ai_service, settings or self._ai_request_settings, **kwargs)

    # async def _invoke_native(self, settings: AIRequestSettings, **kwargs) -> FunctionResult:
    #     self._verify_is_native()

    #     delegate = DelegateHandlers.get_handler(self._delegate_type)
    #     # for python3.9 compatibility (staticmethod is not callable)
    #     if not hasattr(delegate, "__call__"):
    #         delegate = delegate.__func__
    #     new_context = await delegate(self._function, context)

    # return new_context

    # def _verify_is_semantic(self) -> None:
    #     if self._is_semantic:
    #         return

    #     logger.error("The function is not semantic")
    #     raise KernelException(
    #         KernelException.ErrorCodes.InvalidFunctionType,
    #         "Invalid operation, the method requires a semantic function",
    #     )

    # def _verify_is_native(self) -> None:
    #     if not self._is_semantic:
    #         return

    #     logger.error("The function is not native")
    #     raise KernelException(
    #         KernelException.ErrorCodes.InvalidFunctionType,
    #         "Invalid operation, the method requires a native function",
    #     )

    async def invoke_stream(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
        # input: Optional[str] = None,
        # variables: ContextVariables = None,
        # context: Optional["KernelContext"] = None,
        # memory: Optional[SemanticTextMemoryBase] = None,
    ) -> AsyncIterable[List[Union[StreamingKernelContent, Any]]]:
        # from semantic_kernel.orchestration.kernel_context import KernelContext

        # if context is None:
        #     context = KernelContext(
        #         variables=ContextVariables("") if variables is None else variables,
        #         plugin_collection=self._plugin_collection,
        #         memory=memory if memory is not None else NullMemory.instance,
        #     )
        # else:
        #     # If context is passed, we need to merge the variables
        #     if variables is not None:
        #         context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
        #     if memory is not None:
        #         context._memory = memory
        """
        Returns:
            KernelContext -- The context for the function
        """
        # try:
        async for stream_msg in self._stream_function(
            self._ai_service, arguments.execution_settings[self._ai_service], arguments
        ):
            yield stream_msg
        #     if self.is_semantic:
        #         async for stream_msg in self._invoke_semantic_stream(context, settings):
        #             yield stream_msg
        #     else:
        #         async for stream_msg in self._invoke_native_stream(context):
        #             yield stream_msg
        # except Exception as e:
        #     logger.error(f"Error occurred while invoking stream function: {str(e)}")
        #     context.fail(str(e), e)
        #     raise KernelException(
        #         KernelException.ErrorCodes.FunctionInvokeError,
        #         "Error occurred while invoking stream function",
        #     )

    # async def _invoke_semantic_stream(self, arguments: KernelArguments):
    #     self._verify_is_semantic()
    #     # TODO: add kernel to function call for plugins
    #     async for stream_msg in self._stream_function(
    #         self._ai_service, arguments.execution_settings[self._ai_service] or self._ai_request_settings, arguments
    #     ):
    #         yield stream_msg

    # async def _invoke_native_stream(self, settings, **kwargs):
    #     self._verify_is_native()

    #     delegate = DelegateHandlers.get_handler(self._delegate_type)
    #     # for python3.9 compatibility (staticmethod is not callable)
    #     if not hasattr(delegate, "__call__"):
    #         delegate = delegate.__func__

    #     completion = ""
    #     async for partial in delegate(self._function, context):
    #         completion += partial
    #         yield partial

    #     context.variables.update(completion)

    # def _ensure_context_has_plugins(self, context) -> None:
    #     if context.plugins is not None:
    #         return

    #     context.plugins = self._plugin_collection

    def _trace_function_type_Call(self, type: Enum) -> None:
        logger.debug(f"Executing function type {type}: {type.name}")
