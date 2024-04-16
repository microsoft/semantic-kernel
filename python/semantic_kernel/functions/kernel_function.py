# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import functools
import logging
from abc import abstractmethod
from collections.abc import AsyncGenerator
from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.hooks.function.function_hook_context_base import FunctionContext
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

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
    from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
    from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
    from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

logger: logging.Logger = logging.getLogger(__name__)


TEMPLATE_FORMAT_MAP = {
    KERNEL_TEMPLATE_FORMAT_NAME: KernelPromptTemplate,
    HANDLEBARS_TEMPLATE_FORMAT_NAME: HandlebarsPromptTemplate,
    JINJA2_TEMPLATE_FORMAT_NAME: Jinja2PromptTemplate,
}


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

    @classmethod
    def from_prompt(
        cls,
        function_name: str,
        plugin_name: str,
        description: str | None = None,
        prompt: str | None = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: PromptTemplateBase | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        prompt_execution_settings: (
            PromptExecutionSettings | list[PromptExecutionSettings] | dict[str, PromptExecutionSettings] | None
        ) = None,
    ) -> KernelFunctionFromPrompt:
        """
        Create a new instance of the KernelFunctionFromPrompt class.
        """
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
    ) -> KernelFunctionFromMethod:
        """
        Create a new instance of the KernelFunctionFromMethod class.
        """
        from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod

        return KernelFunctionFromMethod(
            plugin_name=plugin_name,
            method=method,
            stream_method=stream_method,
        )

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def plugin_name(self) -> str:
        return self.metadata.plugin_name or ""

    @property
    def fully_qualified_name(self) -> str:
        return self.metadata.fully_qualified_name

    @property
    def description(self) -> str | None:
        return self.metadata.description

    @property
    def is_prompt(self) -> bool:
        return self.metadata.is_prompt

    @property
    def parameters(self) -> list[KernelParameterMetadata]:
        return self.metadata.parameters

    @property
    def return_parameter(self) -> KernelParameterMetadata | None:
        return self.metadata.return_parameter

    async def __call__(
        self,
        kernel: Kernel,
        arguments: KernelArguments | None = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> FunctionResult:
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (Optional[KernelArguments]): The Kernel arguments.
                Optional, defaults to None.
            kwargs (Dict[str, Any]): Additional keyword arguments that will be

        Returns:
            FunctionResult: The result of the function
        """
        return await self.invoke(kernel, arguments, metadata, **kwargs)

    @abstractmethod
    async def _invoke_internal(
        self,
        kernel: Kernel,
        arguments: KernelArguments,
    ) -> FunctionResult:
        pass

    async def invoke(
        self,
        kernel: Kernel,
        arguments: KernelArguments | None = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> "FunctionResult":
        """Invoke the function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
            kwargs (Any): Additional keyword arguments that will be
                added to the KernelArguments.

        Returns:
            FunctionResult: The result of the function
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        KernelFunction._rebuild_context()
        function_context = FunctionContext(function=self, kernel=kernel, arguments=arguments, metadata=metadata)

        stack: list[Callable[[FunctionContext], Coroutine[Any, Any, FunctionContext]]] = [self._wrap()]
        index = 0
        for id, hook in kernel.hooks:
            hook_func = functools.partial(hook.function_filter, next=stack[0])
            stack.append(hook_func)
            index += 1
        result = await stack[-1](function_context)
        return result.result

    def _wrap(self) -> Callable[["FunctionContext"], Coroutine[Any, Any, "FunctionContext"]]:
        async def inner_func(function_context: "FunctionContext") -> "FunctionContext":
            result = await self._invoke_internal(function_context.kernel, function_context.arguments)
            function_context.result = result
            return function_context

        return inner_func

    @staticmethod
    def _rebuild_context() -> None:
        from semantic_kernel.functions.kernel_arguments import KernelArguments  # noqa: F401
        from semantic_kernel.functions.kernel_function import KernelFunction  # noqa: F401
        from semantic_kernel.kernel import Kernel  # noqa: F403 F401

        FunctionContext.model_rebuild()

    @abstractmethod
    def _invoke_internal_stream(
        self,
        kernel: Kernel,
        arguments: KernelArguments,
    ) -> AsyncGenerator[FunctionResult | list[StreamingContentMixin | Any], Any]:
        """Internal invoke method of the the function with the given arguments.

        The abstract method is defined without async because otherwise the typing fails.
        A implementation of this function should be async.
        """
        ...

    async def invoke_stream(
        self,
        kernel: Kernel,
        arguments: KernelArguments | None = None,
        metadata: dict[str, Any] = {},
        **kwargs: Any,
    ) -> AsyncGenerator[FunctionResult | list[StreamingContentMixin | Any], Any]:
        """
        Invoke a stream async function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
            kwargs (Any): Additional keyword arguments that will be
                added to the KernelArguments.

        Yields:
            KernelContent with the StreamingKernelMixin or FunctionResult -- The results of the function,
                if there is an error a FunctionResult is yielded.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        pre_hook_context = await kernel._pre_function_invoke(function=self, arguments=arguments, metadata=metadata)
        if pre_hook_context:
            if pre_hook_context.updated_arguments:
                arguments = pre_hook_context.arguments
            metadata.update(pre_hook_context.metadata)
        exception = None
        try:
            async for partial_result in self._invoke_internal_stream(kernel, arguments):
                if isinstance(partial_result, FunctionResult):
                    yield partial_result
                    break
                yield partial_result
        except Exception as exc:
            exception = exc
            logger.error(f"Error occurred while invoking function {self.name}: {exception}")
            metadata["exception"] = exception
            metadata["arguments"] = arguments
            yield FunctionResult(function=self.metadata, value=None, metadata=metadata)
        # The function_invoked event is not called for stream functions.

    def function_copy(self, plugin_name: str | None = None) -> KernelFunction:
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
