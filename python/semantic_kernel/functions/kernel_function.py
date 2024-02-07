# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import platform
import sys
from functools import wraps
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, AsyncIterable, Callable, Dict, List, Optional, Union

from pydantic import Field, StringConstraints

from semantic_kernel.kernel_pydantic import KernelBaseModel

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
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.prompt_template.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.prompt_template.semantic_function_config import (
    SemanticFunctionConfig,
)

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
    from semantic_kernel.kernel import Kernel

# TODO: is this needed anymore after sync code removal?
if platform.system() == "Windows" and sys.version_info >= (3, 8, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


logger: logging.Logger = logging.getLogger(__name__)


def store_results(chat_prompt: ChatPromptTemplate, results: List["ChatMessageContent"]):
    """Stores specific results in the chat prompt template."""
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
        parameters (List[KernelParameterMetadata]): The parameters for the function.
        return_parameter (Optional[KernelParameterMetadata]): The return parameter for the function.
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
    parameters: List[KernelParameterMetadata] = Field(...)
    return_parameter: Optional[KernelParameterMetadata] = None
    function: Callable[..., Any] = Field(...)
    plugins: Optional["KernelPluginCollection"] = Field(default=None)
    ai_service: Optional[Union[TextCompletionClientBase, ChatCompletionClientBase]] = Field(default=None)
    prompt_execution_settings: PromptExecutionSettings = Field(default_factory=PromptExecutionSettings)
    chat_prompt_template: Optional[ChatPromptTemplate] = Field(default=None)

    def __init__(
        self,
        function: Callable[..., Any],
        parameters: List[KernelParameterMetadata],
        description: str,
        plugin_name: str,
        function_name: str,
        is_semantic: bool,
        return_parameter: Optional[KernelParameterMetadata] = None,
        stream_function: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initializes a new instance of the KernelFunction class

        Args:
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
            function=function,
            parameters=parameters,
            return_parameter=return_parameter,
            description=description,
            plugin_name=plugin_name,
            name=function_name,
            is_semantic=is_semantic,
            stream_function=stream_function,
            chat_prompt_template=chat_prompt_template,
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
        if hasattr(method, "__kernel_function_context_parameters__"):
            for param in method.__kernel_function_context_parameters__:
                assert "name" in param, "Parameter name is empty"
                assert "description" in param, "Parameter description is empty"
                assert "default_value" in param, "Parameter default value is empty"

                parameters.append(
                    KernelParameterMetadata(
                        name=param["name"],
                        description=param["description"],
                        default_value=param["default_value"],
                        type=param.get("type", "str"),
                        required=param.get("required", False),
                    )
                )
        return_param = KernelParameterMetadata(
            name="return",
            description=method.__kernel_function_return_description__
            if hasattr(method, "__kernel_function_return_description__")
            else "",
            default_value=None,
            type=method.__kernel_function_return_type__
            if hasattr(method, "__kernel_function_return_type__")
            else "None",
            required=method.__kernel_function_return_required__
            if hasattr(method, "__kernel_function_return_required__")
            else False,
        )

        function_name = method.__kernel_function_name__
        description = method.__kernel_function_description__

        if hasattr(method, "__kernel_function_streaming__") and method.__kernel_function_streaming__:
            streaming_method = method

            @wraps(method)
            async def _non_streaming_function(*args, **kwargs):
                return [x async for x in streaming_method(*args, **kwargs)]

            method = _non_streaming_function
        else:
            streaming_method = None

        return KernelFunction(
            function=method,
            function_name=function_name,
            plugin_name=plugin_name,
            description=description,
            parameters=parameters,
            return_parameter=return_param,
            stream_function=streaming_method,
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
            function: KernelFunctionMetadata,
            kernel: "Kernel",
            client: Union[TextCompletionClientBase, ChatCompletionClientBase],
            request_settings: PromptExecutionSettings,
            arguments: KernelArguments,
            **kwargs: Dict[str, Any],
        ) -> "FunctionResult":
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")
            try:
                if not function_config.has_chat_prompt:
                    prompt = await function_config.prompt_template.render(kernel, arguments)
                    completion = await client.complete(prompt, request_settings)
                    return FunctionResult(function=function, value=completion)
            except Exception as e:
                logger.error(f"Error occurred while invoking function {function.name}: {e}")
                raise e

            messages = await function_config.prompt_template.render_messages(kernel, arguments)
            try:
                result = await client.complete_chat(messages, request_settings)
                return FunctionResult(function=function, value=result)
            except Exception as exc:
                logger.error(f"Error occurred while invoking function {function.name}: {exc}")
                raise exc

        async def _local_stream_func(
            function: KernelFunctionMetadata,
            kernel: "Kernel",
            client: AIServiceClientBase,
            request_settings: PromptExecutionSettings,
            arguments: KernelArguments,
            **kwargs: Dict[str, Any],
        ) -> AsyncIterable[Union[FunctionResult, List[Union[StreamingKernelContent, Any]]]]:
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            try:
                if function_config.has_chat_prompt:
                    messages = await function_config.prompt_template.render_messages(kernel, arguments)
                    async for partial_content in client.complete_chat_stream(
                        messages=messages, settings=request_settings
                    ):
                        yield partial_content
                else:
                    prompt = await function_config.prompt_template.render(kernel, arguments)
                    async for partial_content in client.complete_stream(prompt, request_settings):
                        yield partial_content

            except Exception as e:
                logger.error(f"Error occurred while invoking function {function.name}: {e}")
                raise e

        semantic_function_params = [
            KernelParameterMetadata(
                name="function",
                description="The function to execute",
                default_value=None,
                type="KernelFunctionMetadata",
                required=True,
                expose=False,
            ),
            KernelParameterMetadata(
                name="kernel",
                description="The kernel",
                default_value=None,
                type="Kernel",
                required=True,
                expose=False,
            ),
            KernelParameterMetadata(
                name="client",
                description="The AI service client",
                default_value=None,
                type="AIServiceClientBase",
                required=True,
                expose=False,
            ),
            KernelParameterMetadata(
                name="request_settings",
                description="The request settings",
                default_value=None,
                type="PromptExecutionSettings",
                required=True,
                expose=False,
            ),
            KernelParameterMetadata(
                name="arguments",
                description="The kernel arguments",
                default_value=None,
                type="KernelArguments",
                required=True,
                expose=False,
            ),
        ]
        semantic_function_params.extend(function_config.prompt_template.get_parameters())
        return KernelFunction(
            function_name=function_name,
            plugin_name=plugin_name,
            description=function_config.prompt_template_config.description,
            function=_local_func,
            parameters=semantic_function_params,
            return_parameter=KernelParameterMetadata(
                name="return",
                description="The completion result",
                default_value=None,
                type="FunctionResult",
                required=True,
            ),
            stream_function=_local_stream_func,
            is_semantic=True,
            chat_prompt_template=function_config.prompt_template if function_config.has_chat_prompt else None,
        )

    def set_default_plugin_collection(self, plugins: "KernelPluginCollection") -> "KernelFunction":
        self.plugins = plugins
        return self

    def set_ai_service(self, ai_service: Callable[[], TextCompletionClientBase]) -> "KernelFunction":
        if ai_service is None:
            raise ValueError("AI LLM service factory cannot be `None`")
        self.ai_service = ai_service()
        return self

    def set_chat_service(self, chat_service: Callable[[], ChatCompletionClientBase]) -> "KernelFunction":
        if chat_service is None:
            raise ValueError("Chat LLM service factory cannot be `None`")
        self.ai_service = chat_service()
        return self

    def set_ai_configuration(self, settings: PromptExecutionSettings) -> "KernelFunction":
        if settings is None:
            raise ValueError("AI LLM request settings cannot be `None`")
        # self._verify_is_semantic()
        self.prompt_execution_settings = settings
        return self

    def set_chat_configuration(self, settings: PromptExecutionSettings) -> "KernelFunction":
        if settings is None:
            raise ValueError("Chat LLM request settings cannot be `None`")
        # self._verify_is_semantic()
        self.prompt_execution_settings = settings
        return self

    def describe(self) -> KernelFunctionMetadata:
        return KernelFunctionMetadata(
            name=self.name,
            plugin_name=self.plugin_name,
            description=self.description or "",
            is_semantic=self.is_semantic,
            parameters=self.parameters,
        )

    async def __call__(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        return await self.invoke(kernel, arguments)

    async def invoke(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        function_arguments = self.gather_function_parameters(kernel, arguments)
        logger.debug("Invoking %s with arguments: %s", self.name, function_arguments)
        try:
            result = self.function(**function_arguments)
            if isawaitable(result):
                result = await result
        except Exception as exc:
            logger.error(f"Error occurred while invoking function {self.name}: {exc}")
            return FunctionResult(
                function=self.describe(), value=None, metadata={"error": exc, "arguments": function_arguments}
            )
        logger.debug("Function result: %s", result)
        logger.debug("Function result type %s", type(result))
        if self.return_parameter and self.return_parameter.type_ and "FunctionResult" in self.return_parameter.type_:
            return result
        return FunctionResult(function=self.describe(), value=result, metadata={"arguments": function_arguments})

    async def invoke_stream(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> AsyncIterable[Union[FunctionResult, List[Union[StreamingKernelContent, Any]]]]:
        """
        Yields:
            StreamingKernelContent or FunctionResult -- The results of the function, if there is an error a FunctionResult is yielded.
        """
        if not self.stream_function:
            raise ValueError("Function does not support streaming")
        function_arguments = self.gather_function_parameters(kernel, arguments)
        logger.debug("Invoking %s with arguments: %s", self.name, function_arguments)
        try:
            async for stream_msg in self.stream_function(**function_arguments):
                yield stream_msg
        except Exception as e:
            logger.error(f"Error occurred while invoking function {self.name}: {e}")
            yield FunctionResult(
                function=self.describe(), value=None, metadata={"error": str(e), "arguments": function_arguments}
            )

    def gather_function_parameters(self, kernel: "Kernel", arguments: "KernelArguments") -> Dict[str, Any]:
        # TODO: replace with service selector
        if arguments.execution_settings and len(arguments.execution_settings) > 1:
            exec_settings = (
                arguments.execution_settings[self.ai_service.ai_model_id]
                if self.ai_service.ai_model_id in arguments.execution_settings
                else self.prompt_execution_settings
            )
        elif arguments.execution_settings and len(arguments.execution_settings) == 1:
            exec_settings = list(arguments.execution_settings.values())[0]
        else:
            exec_settings = self.prompt_execution_settings

        function_arguments = {}
        for param in self.parameters:
            if param.name == "function":
                function_arguments[param.name] = self.describe()
                continue
            if param.name == "kernel":
                function_arguments[param.name] = kernel
                continue
            if param.name == "client":
                function_arguments[param.name] = self.ai_service
                continue
            if param.name == "request_settings":
                function_arguments[param.name] = exec_settings
                continue
            if param.name == "arguments":
                function_arguments[param.name] = arguments
                continue
            if self.is_semantic:
                # a semantic function will use the arguments (KernelArguments) instead of named arguments
                continue
            if param.name in arguments:
                function_arguments[param.name] = arguments[param.name]
                continue
            if param.required:
                raise ValueError(f"Parameter {param.name} is required but not provided in the arguments.")
            logger.debug(f"Parameter {param.name} is not provided, using default value {param.default_value}")
        return function_arguments
