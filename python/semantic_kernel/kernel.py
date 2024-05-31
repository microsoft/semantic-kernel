# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator, AsyncIterable
from copy import copy
from typing import TYPE_CHECKING, Any, Literal, TypeVar

from semantic_kernel.const import METADATA_EXCEPTION_KEY
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.exceptions import (
    KernelFunctionNotFoundError,
    KernelInvokeException,
    OperationCancelledException,
    TemplateSyntaxError,
)
from semantic_kernel.filters.kernel_filters_extension import KernelFilterExtension
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_extension import KernelFunctionExtension
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_types import AI_SERVICE_CLIENT_TYPE
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME
from semantic_kernel.reliability.kernel_reliability_extension import KernelReliabilityExtension
from semantic_kernel.services.ai_service_selector import AIServiceSelector
from semantic_kernel.services.kernel_services_extension import KernelServicesExtension

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction

T = TypeVar("T")


logger: logging.Logger = logging.getLogger(__name__)


class Kernel(KernelFilterExtension, KernelFunctionExtension, KernelServicesExtension, KernelReliabilityExtension):
    """The main Kernel class of Semantic Kernel.

    This is the main entry point for the Semantic Kernel. It provides the ability to run
    semantic/native functions, and manage plugins, memory, and AI services.

    Attributes:
        plugins (dict[str, KernelPlugin] | None): The plugins to be used by the kernel
        services (dict[str, AIServiceClientBase]): The services to be used by the kernel
        ai_service_selector (AIServiceSelector): The AI service selector to be used by the kernel
        retry_mechanism (RetryMechanismBase): The retry mechanism to be used by the kernel
    """

    def __init__(
        self,
        plugins: KernelPlugin | dict[str, KernelPlugin] | list[KernelPlugin] | None = None,
        services: (
            AI_SERVICE_CLIENT_TYPE | list[AI_SERVICE_CLIENT_TYPE] | dict[str, AI_SERVICE_CLIENT_TYPE] | None
        ) = None,
        ai_service_selector: AIServiceSelector | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new instance of the Kernel class.

        Args:
            plugins (KernelPlugin | dict[str, KernelPlugin] | list[KernelPlugin] | None):
                The plugins to be used by the kernel, will be rewritten to a dict with plugin name as key
            services (AIServiceClientBase | list[AIServiceClientBase] | dict[str, AIServiceClientBase] | None):
                The services to be used by the kernel, will be rewritten to a dict with service_id as key
            ai_service_selector (AIServiceSelector | None):
                The AI service selector to be used by the kernel,
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

    async def invoke_stream(
        self,
        function: "KernelFunction | None" = None,
        arguments: KernelArguments | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        metadata: dict[str, Any] = {},
        return_function_results: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingContentMixin"] | FunctionResult | list[FunctionResult], Any]:
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
        if not function:
            if not function_name or not plugin_name:
                raise KernelFunctionNotFoundError("No function(s) or function- and plugin-name provided")
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
            yield FunctionResult(function=function.metadata, value=output_function_result)

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
                raise KernelFunctionNotFoundError("No function, or function name and plugin name provided")
            function = self.get_function(plugin_name, function_name)

        try:
            return await function.invoke(kernel=self, arguments=arguments, metadata=metadata)
        except OperationCancelledException as exc:
            logger.info(f"Operation cancelled during function invocation. Message: {exc}")
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
        """Invoke a function from the provided prompt.

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
        return await self.invoke(function=function, arguments=arguments)

    async def invoke_prompt_stream(
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
        return_function_results: bool | None = False,
        **kwargs: Any,
    ) -> AsyncIterable[list["StreamingContentMixin"] | FunctionResult | list[FunctionResult]]:
        """Invoke a function from the provided prompt and stream the results.

        Args:
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            prompt (str): The prompt to use
            arguments (KernelArguments | None): The arguments to pass to the function(s), optional
            template_format (str | None): The format of the prompt template
            return_function_results (bool): If True, the function results are yielded as a list[FunctionResult]
            kwargs (dict[str, Any]): arguments that can be used instead of supplying KernelArguments

        Returns:
            AsyncIterable[StreamingContentMixin]: The content of the stream of the last function provided.
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

        function_result: list[list["StreamingContentMixin"] | Any] = []

        async for stream_message in self.invoke_stream(function=function, arguments=arguments):
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
            yield FunctionResult(function=function.metadata, value=output_function_result)
