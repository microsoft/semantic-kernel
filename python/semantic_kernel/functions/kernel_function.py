# Copyright (c) Microsoft. All rights reserved.

import logging
import time
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Mapping, Sequence
from copy import copy, deepcopy
from inspect import isasyncgen, isgenerator
from typing import TYPE_CHECKING, Any

from opentelemetry import metrics, trace
from opentelemetry.semconv.attributes.error_attributes import ERROR_TYPE
from pydantic import Field

from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.filters.kernel_filters_extension import _rebuild_function_invocation_context
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
from semantic_kernel.prompt_template.handlebars_prompt_template import HandlebarsPromptTemplate
from semantic_kernel.prompt_template.jinja2_prompt_template import Jinja2PromptTemplate
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
    from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
    from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

# Logger, tracer and meter for observability
logger: logging.Logger = logging.getLogger(__name__)
tracer: trace.Tracer = trace.get_tracer(__name__)
meter: metrics.Meter = metrics.get_meter_provider().get_meter(__name__)
MEASUREMENT_FUNCTION_TAG_NAME: str = "semantic_kernel.function.name"

TEMPLATE_FORMAT_MAP: dict[TEMPLATE_FORMAT_TYPES, type[PromptTemplateBase]] = {
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

    invocation_duration_histogram: metrics.Histogram = Field(
        default_factory=_create_function_duration_histogram, exclude=True
    )
    streaming_duration_histogram: metrics.Histogram = Field(
        default_factory=_create_function_streaming_duration_histogram, exclude=True
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
        prompt_execution_settings: (
            "PromptExecutionSettings | Sequence[PromptExecutionSettings] | Mapping[str, PromptExecutionSettings] | None"
        ) = None,
    ) -> "KernelFunctionFromPrompt":
        """Create a new instance of the KernelFunctionFromPrompt class."""
        from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt

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
        from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod

        return KernelFunctionFromMethod(
            plugin_name=plugin_name,
            method=method,
            stream_method=stream_method,
        )

    @property
    def name(self) -> str:
        """The name of the function."""
        return self.metadata.name

    @property
    def plugin_name(self) -> str:
        """The name of the plugin that contains this function."""
        return self.metadata.plugin_name or ""

    @property
    def fully_qualified_name(self) -> str:
        """The fully qualified name of the function."""
        return self.metadata.fully_qualified_name

    @property
    def description(self) -> str | None:
        """The description of the function."""
        return self.metadata.description

    @property
    def is_prompt(self) -> bool:
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
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> FunctionResult | None:
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments | None): The Kernel arguments.
                Optional, defaults to None.
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Dict[str, Any]): Additional keyword arguments that will be

        Returns:
            FunctionResult: The result of the function
        """
        return await self.invoke(kernel, arguments, metadata, **kwargs)

    @abstractmethod
    async def _invoke_internal(self, context: FunctionInvocationContext) -> None:
        """Internal invoke method of the the function with the given arguments.

        This function should be implemented by the subclass.
        It relies on updating the context with the result from the function.

        Args:
            context (FunctionInvocationContext): The invocation context.

        """
        pass

    async def invoke(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments | None" = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "FunctionResult | None":
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
            metadata (Dict[str, Any]): Additional metadata.
            kwargs (Any): Additional keyword arguments that will be
                added to the KernelArguments.

        Returns:
            FunctionResult: The result of the function
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        _rebuild_function_invocation_context()
        function_context = FunctionInvocationContext(function=self, kernel=kernel, arguments=arguments)

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

    async def invoke_stream(
        self,
        kernel: "Kernel",
        arguments: "KernelArguments | None" = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "AsyncGenerator[FunctionResult | list[StreamingContentMixin | Any], Any]":
        """Invoke a stream async function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
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
        function_context = FunctionInvocationContext(
            function=self, kernel=kernel, arguments=arguments, is_streaming=True
        )

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
