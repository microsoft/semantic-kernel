# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, AsyncIterable, Callable, Dict, List, Optional, Union

from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
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

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
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
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: Optional["PromptTemplateBase"] = None,
        prompt_template_config: Optional["PromptTemplateConfig"] = None,
        prompt_execution_settings: Optional[
            Union["PromptExecutionSettings", List["PromptExecutionSettings"], Dict[str, "PromptExecutionSettings"]]
        ] = None,
    ) -> "KernelFunctionFromPrompt":
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
        plugin_name: Optional[str] = None,
        stream_method: Optional[Callable[..., Any]] = None,
    ) -> "KernelFunctionFromMethod":
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

    async def __call__(
        self,
        kernel: "Kernel",
        arguments: Optional[KernelArguments] = None,
        **kwargs: Any,
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

    @abstractmethod
    async def _invoke_internal(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        pass

    async def invoke(
        self,
        kernel: "Kernel",
        arguments: Optional[KernelArguments] = None,
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
        try:
            return await self._invoke_internal(kernel, arguments)
        except Exception as exc:
            logger.error(f"Error occurred while invoking function {self.name}: {exc}")
            return FunctionResult(
                function=self.metadata, value=None, metadata={"exception": exc, "arguments": arguments}
            )

    @abstractmethod
    async def _invoke_internal_stream(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> AsyncIterable[Union[FunctionResult, List[Union[StreamingKernelContent, Any]]]]:
        pass

    async def invoke_stream(
        self,
        kernel: "Kernel",
        arguments: Optional[KernelArguments] = None,
        **kwargs: Any,
    ) -> AsyncIterable[Union[FunctionResult, List[Union[StreamingKernelContent, Any]]]]:
        """
        Invoke a stream async function with the given arguments.

        Args:
            kernel (Kernel): The kernel
            arguments (KernelArguments): The Kernel arguments
            kwargs (Any): Additional keyword arguments that will be
                added to the KernelArguments.

        Yields:
            StreamingKernelContent or FunctionResult -- The results of the function,
                if there is an error a FunctionResult is yielded.
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        try:
            async for partial_result in self._invoke_internal_stream(kernel, arguments):
                yield partial_result
        except Exception as e:
            logger.error(f"Error occurred while invoking function {self.name}: {e}")
            yield FunctionResult(function=self.metadata, value=None, metadata={"exception": e, "arguments": arguments})
