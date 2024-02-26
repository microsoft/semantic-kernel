# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import platform
import sys
from functools import wraps
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, AsyncIterable, Callable, Dict, List, Optional, Union

from pydantic import Field, ValidationError, field_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel

if sys.version_info >= (3, 9):
    pass
else:
    pass

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.naming import generate_random_ascii_name

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

# TODO: is this needed anymore after sync code removal?
if platform.system() == "Windows" and sys.version_info >= (3, 8, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger: logging.Logger = logging.getLogger(__name__)


class KernelFunction(KernelBaseModel):
    """
    Semantic Kernel function.

    Attributes:
        name (str): The name of the function. Must be upper/lower case letters and
            underscores with a minimum length of 1.
        plugin_name (str): The name of the plugin that contains this function. Must be upper/lower
            case letters and underscores with a minimum length of 1.
        description (Optional[str]): The description of the function.
        is_prompt (bool): Whether the function is semantic.
        stream_function (Optional[Callable[..., Any]]): The stream function for the function.
        parameters (List[KernelParameterMetadata]): The parameters for the function.
        return_parameter (Optional[KernelParameterMetadata]): The return parameter for the function.
        function (Callable[..., Any]): The function to call.
        prompt_execution_settings (PromptExecutionSettings): The AI prompt execution settings.
        prompt_template_config (PromptTemplateConfig): The prompt template configuration.
        metadata (Optional[KernelFunctionMetadata]): The metadata for the function.
    """

    # some attributes are now properties, still listed here for documentation purposes

    metadata: KernelFunctionMetadata
    function: Callable[..., Any]

    stream_function: Optional[Callable[..., Any]] = None
    prompt_template_config: Optional[PromptTemplateConfig] = Field(default_factory=PromptTemplateConfig)
    prompt_execution_settings: Dict[str, PromptExecutionSettings] = Field(default_factory=dict)

    def __init__(
        self,
        function_name: str,
        plugin_name: str,
        description: str,
        function: Callable[..., Any],
        is_prompt: bool,
        parameters: List[KernelParameterMetadata],
        return_parameter: Optional[KernelParameterMetadata] = None,
        stream_function: Optional[Callable[..., Any]] = None,
        prompt_execution_settings: Optional[
            Union[PromptExecutionSettings, List[PromptExecutionSettings], Dict[str, PromptExecutionSettings]]
        ] = None,
        prompt_template_config: Optional[PromptTemplateConfig] = None,
    ) -> None:
        """
        Initializes a new instance of the KernelFunction class

        Args:
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            description (str): The description for the function
            function (Callable[..., Any]): The function
            is_prompt (bool): Whether the function is semantic
            parameters (List[KernelParameterMetadata]): The parameters for the function
            return_parameter (Optional[KernelParameterMetadata]): The return parameter of the function
            stream_function (Optional[Callable[..., Any]]): The stream function for the function
            prompt_execution_settings (Optional): instance, list or dict of PromptExecutionSettings to be used by the
            function, can also be supplied through prompt_template_config,
            but the supplied one is used if both are present.
            prompt_template_config (Optional[PromptTemplateConfig]): the prompt template config.
        """
        try:
            metadata = KernelFunctionMetadata(
                name=function_name,
                description=description,
                parameters=parameters,
                return_parameter=return_parameter,
                is_prompt=is_prompt,
                plugin_name=plugin_name,
            )
        except ValidationError as exc:
            # reraise the exception to clarify it comes from KernelFunction init
            raise exc

        args: Dict[str, Any] = {
            "metadata": metadata,
            "function": function,
        }
        if stream_function:
            args["stream_function"] = stream_function
        if return_parameter:
            args["return_parameter"] = return_parameter
        if prompt_template_config:
            args["prompt_template_config"] = prompt_template_config
        if prompt_execution_settings:
            args["prompt_execution_settings"] = prompt_execution_settings
        elif prompt_template_config:
            args["prompt_execution_settings"] = prompt_template_config.execution_settings
        super().__init__(**args)

    @field_validator("prompt_execution_settings", mode="before")
    @classmethod
    def rewrite_execution_settings(
        cls,
        prompt_execution_settings: Optional[
            Union[PromptExecutionSettings, List[PromptExecutionSettings], Dict[str, PromptExecutionSettings]]
        ],
    ) -> Dict[str, PromptExecutionSettings]:
        """Rewrite execution settings to a dictionary."""
        if not prompt_execution_settings:
            return {}
        if isinstance(prompt_execution_settings, PromptExecutionSettings):
            return {prompt_execution_settings.service_id or "default": prompt_execution_settings}
        if isinstance(prompt_execution_settings, list):
            return {s.service_id or "default": s for s in prompt_execution_settings}
        return prompt_execution_settings

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def plugin_name(self) -> str:
        return self.metadata.plugin_name

    @property
    def description(self) -> Optional[str]:
        return self.metadata.description

    @property
    def is_prompt(self) -> bool:
        return self.metadata.is_prompt

    @property
    def parameters(self) -> List[KernelParameterMetadata]:
        return self.metadata.parameters

    @property
    def return_parameter(self) -> Optional[KernelParameterMetadata]:
        return self.metadata.return_parameter

    @staticmethod
    def from_native_method(method: Callable[..., Any], plugin_name: str) -> "KernelFunction":
        """
        Create a KernelFunction from a method.

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

        parameters: List["KernelParameterMetadata"] = []
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
                        expose=True,
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

        if getattr(method, "__kernel_function_streaming__", False):
            streaming_method = method

            @wraps(method)
            async def _non_streaming_function(*args, **kwargs):
                return [x async for x in streaming_method(*args, **kwargs)]

            method = _non_streaming_function
        else:
            streaming_method = None

        return KernelFunction(
            function_name=function_name or f"f_{generate_random_ascii_name()}",
            plugin_name=plugin_name or f"p_{generate_random_ascii_name()}",
            description=description,
            function=method,
            parameters=parameters,
            return_parameter=return_param,
            stream_function=streaming_method,
            is_prompt=False,
        )

    @staticmethod
    def from_prompt(
        prompt: str,
        function_name: Optional[str] = None,
        plugin_name: Optional[str] = None,
        description: Optional[str] = None,
        template_format: Optional[str] = None,
        prompt_template: Optional[PromptTemplateBase] = None,
        prompt_execution_settings: Optional[PromptExecutionSettings] = None,
        prompt_template_config: Optional[PromptTemplateConfig] = None,
    ) -> "KernelFunction":
        """
        Create a Kernel Function from a prompt

        Args:
            prompt (str): The prompt
            execution_settings (Optional[PromptExecutionSettings]): The execution settings
            plugin_name (Optional[str]): The name of the plugin
            function_name (Optional[str]): The name of the function
            description (Optional[str]): The description of the function
            template_format (Optional[str]): The template format
            prompt_template (Optional[PromptTemplateBase]): The prompt template
            prompt_template_config (Optional[PromptTemplateConfig]): The prompt template configuration

        Returns:
            KernelFunction: The kernel function
        """

        if prompt_template and not template_format:
            raise ValueError(f"Template format cannot be `None` when providing a {prompt_template}")

        if not prompt_template_config:
            prompt_template_config = PromptTemplateConfig(
                name=function_name,
                description=description if description else "Semantic function, unknown purpose",
                template=prompt,
                template_format=template_format if template_format else "semantic-kernel",
                execution_settings=prompt_execution_settings
                if prompt_execution_settings
                else PromptExecutionSettings(),
            )

        if not prompt_template:
            prompt_template = KernelPromptTemplate(prompt_template_config=prompt_template_config)

        async def _local_func(
            function: KernelFunctionMetadata,
            kernel: "Kernel",
            service: Union[TextCompletionClientBase, ChatCompletionClientBase],
            execution_settings: PromptExecutionSettings,
            arguments: KernelArguments,
        ) -> "FunctionResult":
            if service is None:
                raise ValueError("AI LLM service cannot be `None`")

            prompt = await prompt_template.render(kernel, arguments)

            if isinstance(service, ChatCompletionClientBase):
                chat_history = ChatHistory.from_rendered_prompt(prompt, service.get_chat_message_content_class())
                try:
                    completions = await service.complete_chat(chat_history, execution_settings)
                    # this can be expanded for auto-invoking function calls
                    # store_results function is in utils.chat
                    # chat_history = store_results(chat_history=chat_history, results=completions)
                except Exception as exc:
                    logger.error(f"Error occurred while invoking function {function.name}: {exc}")
                    raise exc

                return FunctionResult(
                    function=function,
                    value=completions,
                    metadata={
                        "messages": chat_history,
                        "arguments": arguments,
                        "metadata": [completion.metadata for completion in completions],
                    },
                )

            if isinstance(service, TextCompletionClientBase):
                try:
                    completions = await service.complete(prompt, execution_settings)
                except Exception as e:
                    logger.error(f"Error occurred while invoking function {function.name}: {e}")
                    raise e

                return FunctionResult(
                    function=function,
                    value=completions,
                    metadata={
                        "prompt": prompt,
                        "arguments": arguments,
                        "metadata": [completion.metadata for completion in completions],
                    },
                )

            raise ValueError(f"Service `{type(service)}` is not a valid AI service")

        async def _local_stream_func(
            function: KernelFunctionMetadata,
            kernel: "Kernel",
            service: Union[TextCompletionClientBase, ChatCompletionClientBase],
            execution_settings: PromptExecutionSettings,
            arguments: KernelArguments,
        ) -> AsyncIterable[Union[FunctionResult, List[StreamingKernelContent]]]:
            if service is None:
                raise ValueError("AI LLM service cannot be `None`")

            prompt = await prompt_template.render(kernel, arguments)

            if isinstance(service, ChatCompletionClientBase):
                chat_history = ChatHistory.from_rendered_prompt(prompt, service.get_chat_message_content_class())
                try:
                    async for partial_content in service.complete_chat_stream(
                        chat_history=chat_history, settings=execution_settings
                    ):
                        yield partial_content
                    return
                except Exception as e:
                    logger.error(f"Error occurred while invoking function {function.name}: {e}")
                    yield FunctionResult(function=function, value=None, metadata={"exception": e})
            if isinstance(service, TextCompletionClientBase):
                try:
                    async for partial_content in service.complete_stream(prompt, execution_settings):
                        yield partial_content
                    return
                except Exception as e:
                    logger.error(f"Error occurred while invoking function {function.name}: {e}")
                    yield FunctionResult(function=function, value=None, metadata={"exception": e})

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
                name="service",
                description="The AI service client",
                default_value=None,
                type="AIServiceClientBase",
                required=True,
                expose=False,
            ),
            KernelParameterMetadata(
                name="execution_settings",
                description="The execution settings",
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
        semantic_function_params.extend(prompt_template_config.get_kernel_parameter_metadata())
        return KernelFunction(
            function_name=function_name or prompt_template_config.name or f"f_{generate_random_ascii_name()}",
            plugin_name=plugin_name or f"p_{generate_random_ascii_name()}",
            description=description or prompt_template_config.description or "Semantic function, unknown purpose",
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
            is_prompt=True,
            prompt_template_config=prompt_template_config,
            prompt_execution_settings=prompt_execution_settings,
        )

    async def __call__(
        self,
        kernel: "Kernel",
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> "FunctionResult":
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (Optional[KernelArguments]): The Kernel arguments.
                Optional, defaults to None.
            kwargs (Dict[str, Any]): Additional keyword arguments that will be

        Returns:
            FunctionResult: The result of the function
        """
        return await self.invoke(kernel, arguments, **kwargs)

    async def invoke(
        self,
        kernel: "Kernel",
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> "FunctionResult":
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
            kwargs (Dict[str, Any]): Additional keyword arguments that will be
                added to the KernelArguments.

        Returns:
            FunctionResult: The result of the function
        """
        if not arguments:
            arguments = KernelArguments(**kwargs)
        function_arguments = self.gather_function_parameters(kernel, arguments)
        logger.debug("Invoking %s with arguments: %s", self.name, function_arguments)
        try:
            result = self.function(**function_arguments)
            if isawaitable(result):
                result = await result
        except Exception as exc:
            logger.error(f"Error occurred while invoking function {self.name}: {exc}")
            return FunctionResult(
                function=self.metadata, value=None, metadata={"error": exc, "arguments": function_arguments}
            )
        logger.debug("Function result: %s", result)
        logger.debug("Function result type %s", type(result))
        if self.return_parameter and self.return_parameter.type_ and "FunctionResult" in self.return_parameter.type_:
            return result
        return FunctionResult(function=self.metadata, value=result, metadata={"arguments": function_arguments})

    async def invoke_stream(
        self,
        kernel: "Kernel",
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> AsyncIterable[Union[FunctionResult, List[Union[StreamingKernelContent, Any]]]]:
        """
        Invoke a stream async function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
            kwargs (Dict[str, Any]): Additional keyword arguments that will be
                added to the KernelArguments.

        Yields:
            StreamingKernelContent or FunctionResult -- The results of the function,
                if there is an error a FunctionResult is yielded.
        """
        if not arguments:
            arguments = KernelArguments(**kwargs)
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
                function=self.metadata, value=None, metadata={"error": e, "arguments": function_arguments}
            )

    def gather_function_parameters(self, kernel: "Kernel", arguments: "KernelArguments") -> Dict[str, Any]:
        """Gathers the function parameters from the arguments."""
        if self.prompt_template_config:
            arguments = self.add_default_values(arguments, self.prompt_template_config)
        function_arguments: Dict[str, Any] = {}
        for param in self.parameters:
            if param.name == "function":
                function_arguments[param.name] = self.metadata
                continue
            if param.name == "kernel":
                function_arguments[param.name] = kernel
                continue
            if param.name == "service":
                function_arguments[param.name] = kernel.select_ai_service(self, arguments)[0]
                continue
            if param.name == "execution_settings":
                function_arguments[param.name] = kernel.select_ai_service(self, arguments)[1]
                continue
            if param.name == "arguments":
                function_arguments[param.name] = arguments
                continue
            if param.name == "prompt_template_config":
                function_arguments[param.name] = self.prompt_template_config
                continue
            if param.type_ == "ChatHistory":
                if param.name in arguments:
                    function_arguments[param.name] = arguments[param.name]
                else:
                    function_arguments[param.name] = ChatHistory()
                continue
            if self.is_prompt:
                # a semantic function will use the arguments (KernelArguments) instead of named arguments
                continue
            if param.name in arguments:
                function_arguments[param.name] = arguments[param.name]
                continue
            if param.required:
                raise ValueError(f"Parameter {param.name} is required but not provided in the arguments.")
            logger.debug(f"Parameter {param.name} is not provided, using default value {param.default_value}")
        return function_arguments

    def add_default_values(
        self, arguments: KernelArguments, prompt_template_config: PromptTemplateConfig
    ) -> KernelArguments:
        """Adds default values to the arguments."""
        for parameter in prompt_template_config.input_variables:
            if parameter.name not in arguments and parameter.default not in {None, "", False, 0}:
                arguments[parameter.name] = parameter.default
        return arguments
