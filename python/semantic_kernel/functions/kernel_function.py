# Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
import logging
import time
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable
from copy import copy, deepcopy
from inspect import isasyncgen, isgenerator
from typing import TYPE_CHECKING, Any

from opentelemetry import metrics, trace
from opentelemetry.semconv.attributes.error_attributes import ERROR_TYPE
from pydantic import Field

from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import (
    FunctionInvocationContext,
)
from semantic_kernel.filters.kernel_filters_extension import (
    _rebuild_function_invocation_context,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_log_messages import KernelFunctionLogMessages
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.const import (
    HANDLEBARS_TEMPLATE_FORMAT_NAME,
    JINJA2_TEMPLATE_FORMAT_NAME,
    KERNEL_TEMPLATE_FORMAT_NAME,
    TEMPLATE_FORMAT_TYPES,
)
from semantic_kernel.prompt_template.handlebars_prompt_template import (
    HandlebarsPromptTemplate,
)
from semantic_kernel.prompt_template.jinja2_prompt_template import Jinja2PromptTemplate
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )
    from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
    from semantic_kernel.functions.kernel_function_from_method import (
        KernelFunctionFromMethod,
    )
    from semantic_kernel.functions.kernel_function_from_prompt import (
        KernelFunctionFromPrompt,
    )
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
    from semantic_kernel.prompt_template.prompt_template_config import (
        PromptTemplateConfig,
    )

# Logger, tracer and meter for observability
logger: logging.Logger = logging.getLogger(__name__)
tracer: trace.Tracer = trace.get_tracer(__name__)
meter: metrics.Meter = metrics.get_meter_provider().get_meter(__name__)
MEASUREMENT_FUNCTION_TAG_NAME: str = "semantic_kernel.function.name"

TEMPLATE_FORMAT_MAP = {
    KERNEL_TEMPLATE_FORMAT_NAME: KernelPromptTemplate,
    HANDLEBARS_TEMPLATE_FORMAT_NAME: HandlebarsPromptTemplate,
    JINJA2_TEMPLATE_FORMAT_NAME: Jinja2PromptTemplate,
}


def _create_function_duration_histogram():
    return meter.create_histogram(
        "semantic_kernel.function.invocation.duration",
        unit="s",
        description="Measures the duration of a function's execution",
    )


def _create_function_streaming_duration_histogram():
    return meter.create_histogram(
        "semantic_kernel.function.streaming.duration",
        unit="s",
        description="Measures the duration of a function's streaming execution",
    )


class KernelFunction(KernelBaseModel):
    """Semantic Kernel function.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

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
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    invocation_duration_histogram: metrics.Histogram = Field(default_factory=_create_function_duration_histogram)
    streaming_duration_histogram: metrics.Histogram = Field(
        default_factory=_create_function_streaming_duration_histogram
    )

    @classmethod
    def from_prompt(
        cls,
        function_name: str,
        plugin_name: str,
        description: str | None = None,
        prompt: str | None = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: "PromptTemplateBase | None " = None,
        prompt_template_config: "PromptTemplateConfig | None" = None,
        prompt_execution_settings: "PromptExecutionSettings | list[PromptExecutionSettings] | dict[str, PromptExecutionSettings] | None" = None,
    ) -> "KernelFunctionFromPrompt":
        """Create a new instance of the KernelFunctionFromPrompt class."""
        from semantic_kernel.functions.kernel_function_from_prompt import (
            KernelFunctionFromPrompt,
        )

        return KernelFunctionFromPrompt(
            function_name=function_name,
            plugin_name=plugin_name,
            description=description,
            prompt=prompt,
            template_format=template_format,
            prompt_template=prompt_template,
            prompt_template_config=prompt_template_config,
            prompt_execution_settings=prompt_execution_settings,
        )

    @classmethod
    def from_method(
        cls,
        method: Callable[..., Any],
        plugin_name: str | None = None,
        stream_method: Callable[..., Any] | None = None,
    ) -> "KernelFunctionFromMethod":
        """Create a new instance of the KernelFunctionFromMethod class."""
        from semantic_kernel.functions.kernel_function_from_method import (
            KernelFunctionFromMethod,
        )

        return KernelFunctionFromMethod(
            plugin_name=plugin_name,
            method=method,
            stream_method=stream_method,
        )

    @property
    def name(self) -> str:
        """The name of the function."""
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        return self.metadata.name

    @property
    def plugin_name(self) -> str:
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        """The name of the plugin that contains this function."""
        return self.metadata.plugin_name or ""

    @property
    def fully_qualified_name(self) -> str:
        """The fully qualified name of the function."""
        return self.metadata.fully_qualified_name

    @property
    def description(self) -> str | None:
        """The description of the function."""
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
        return self.metadata.plugin_name

    @property
    def description(self) -> Optional[str]:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        return self.metadata.description

    @property
    def is_prompt(self) -> bool:
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        """Whether the function is based on a prompt."""
        return self.metadata.is_prompt

    @property
    def parameters(self) -> list["KernelParameterMetadata"]:
        """The parameters for the function."""
        return self.metadata.parameters

    @property
    def return_parameter(self) -> "KernelParameterMetadata | None":
        """The return parameter for the function."""
        return self.metadata.return_parameter

    async def __call__(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments | None" = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> FunctionResult | None:
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            arguments (KernelArguments | None): The Kernel arguments.
                Optional, defaults to None.
            metadata (Dict[str, Any]): Additional metadata.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            arguments (KernelArguments | None): The Kernel arguments.
                Optional, defaults to None.
            metadata (Dict[str, Any]): Additional metadata.
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
            arguments (KernelArguments | None): The Kernel arguments.
                Optional, defaults to None.
            metadata (Dict[str, Any]): Additional metadata.
=======
            arguments (Optional[KernelArguments]): The Kernel arguments.
                Optional, defaults to None.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
            kwargs (Dict[str, Any]): Additional keyword arguments that will be

        Returns:
            FunctionResult: The result of the function
        """
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        return await self.invoke(kernel, arguments, metadata, **kwargs)

    @abstractmethod
    async def _invoke_internal(self, context: FunctionInvocationContext) -> None:
        """Internal invoke method of the the function with the given arguments.

        This function should be implemented by the subclass.
        It relies on updating the context with the result from the function.

        Args:
            context (FunctionInvocationContext): The invocation context.

        """
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
        return await self.invoke(kernel, arguments, **kwargs)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
        return await self.invoke(kernel, arguments, **kwargs)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
        return await self.invoke(kernel, arguments, **kwargs)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

    async def invoke(
        self,
        kernel: "Kernel",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        arguments: "KernelArguments | None" = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> "FunctionResult | None":
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> "FunctionResult":
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
=======
>>>>>>> Stashed changes
=======
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
=======
            kwargs (Dict[str, Any]): Additional keyword arguments that will be
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
                added to the KernelArguments.

        Returns:
            FunctionResult: The result of the function
        """
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        _rebuild_function_invocation_context()
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments
        )
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        _rebuild_function_invocation_context()
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments
        )
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        _rebuild_function_invocation_context()
<<<<<<< main
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments
        )
=======
        function_context = FunctionInvocationContext(function=self, kernel=kernel, arguments=arguments)
>>>>>>> ms/features/bugbash-prep
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        with tracer.start_as_current_span(self.fully_qualified_name) as current_span:
            KernelFunctionLogMessages.log_function_invoking(logger, self.fully_qualified_name)
            KernelFunctionLogMessages.log_function_arguments(logger, arguments)

            attributes = {MEASUREMENT_FUNCTION_TAG_NAME: self.fully_qualified_name}
            starting_time_stamp = time.perf_counter()
            try:
                stack = kernel.construct_call_stack(
                    filter_type=FilterTypes.FUNCTION_INVOCATION,
                    inner_function=self._invoke_internal,
                )
                await stack(function_context)

                KernelFunctionLogMessages.log_function_invoked_success(logger, self.fully_qualified_name)
                KernelFunctionLogMessages.log_function_result_value(logger, function_context.result)

                return function_context.result
            except Exception as e:
                self._handle_exception(current_span, e, attributes)
                raise e
            finally:
                duration = time.perf_counter() - starting_time_stamp
                self.invocation_duration_histogram.record(duration, attributes)
                KernelFunctionLogMessages.log_function_completed(logger, duration)

    @abstractmethod
    async def _invoke_internal_stream(self, context: FunctionInvocationContext) -> None:
        """Internal invoke method of the the function with the given arguments.

        The abstract method is defined without async because otherwise the typing fails.
        A implementation of this function should be async.
        """
        ...
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

    async def invoke_stream(
        self,
        kernel: "Kernel",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        arguments: "KernelArguments | None" = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> "AsyncGenerator[FunctionResult | list[StreamingContentMixin | Any], Any]":
        """Invoke a stream async function with the given arguments.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
=======
>>>>>>> Stashed changes
        arguments: Optional[KernelArguments] = None,
        **kwargs: Dict[str, Any],
    ) -> AsyncIterable[Union[FunctionResult, List[Union[StreamingKernelContent, Any]]]]:
        """
        Invoke a stream async function with the given arguments.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
                added to the KernelArguments.

        Yields:
            KernelContent with the StreamingKernelMixin or FunctionResult:
                The results of the function,
                if there is an error a FunctionResult is yielded.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        _rebuild_function_invocation_context()
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments
        )
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments
        )
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments
        )
=======
        function_context = FunctionInvocationContext(function=self, kernel=kernel, arguments=arguments)
>>>>>>> ms/features/bugbash-prep
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        with tracer.start_as_current_span(self.fully_qualified_name) as current_span:
            KernelFunctionLogMessages.log_function_streaming_invoking(logger, self.fully_qualified_name)
            KernelFunctionLogMessages.log_function_arguments(logger, arguments)

            attributes = {MEASUREMENT_FUNCTION_TAG_NAME: self.fully_qualified_name}
            starting_time_stamp = time.perf_counter()
            try:
                stack = kernel.construct_call_stack(
                    filter_type=FilterTypes.FUNCTION_INVOCATION,
                    inner_function=self._invoke_internal_stream,
                )
                await stack(function_context)

                if function_context.result is not None:
                    if isasyncgen(function_context.result.value):
                        async for partial in function_context.result.value:
                            yield partial
                    elif isgenerator(function_context.result.value):
                        for partial in function_context.result.value:
                            yield partial
                    else:
                        yield function_context.result
            except Exception as e:
                self._handle_exception(current_span, e, attributes)
                raise e
            finally:
                duration = time.perf_counter() - starting_time_stamp
                self.streaming_duration_histogram.record(duration, attributes)
                KernelFunctionLogMessages.log_function_streaming_completed(logger, duration)

    def function_copy(self, plugin_name: str | None = None) -> "KernelFunction":
        """Copy the function, can also override the plugin_name.

        Args:
            plugin_name (str): The new plugin name.

        Returns:
            KernelFunction: The copied function.
        """
        cop: KernelFunction = copy(self)
        cop.metadata = deepcopy(self.metadata)
        if plugin_name:
            cop.metadata.plugin_name = plugin_name
        return cop

    def _handle_exception(self, current_span: trace.Span, exception: Exception, attributes: dict[str, str]) -> None:
        """Handle the exception.

        Args:
            current_span (trace.Span): The current span.
            exception (Exception): The exception.
            attributes (Attributes): The attributes to be modified.
        """
        attributes[ERROR_TYPE] = type(exception).__name__

        current_span.record_exception(exception)
        current_span.set_attribute(ERROR_TYPE, type(exception).__name__)
        current_span.set_status(trace.StatusCode.ERROR, description=str(exception))

        KernelFunctionLogMessages.log_function_error(logger, exception)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
