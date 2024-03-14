# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, AsyncIterable, Dict, List, Optional, Union

from pydantic import Field, ValidationError, model_validator

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP, KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME, TEMPLATE_FORMAT_TYPES
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)

PROMPT_RETURN_PARAM = KernelParameterMetadata(
    name="return",
    description="The completion result",
    default_value=None,
    type="FunctionResult",
    is_required=True,
)


class KernelFunctionFromPrompt(KernelFunction):
    """Semantic Kernel Function from a prompt."""

    prompt_template: PromptTemplateBase
    prompt_execution_settings: Dict[str, PromptExecutionSettings] = Field(default_factory=dict)

    def __init__(
        self,
        function_name: str,
        plugin_name: str,
        description: Optional[str] = None,
        prompt: Optional[str] = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: Optional[PromptTemplateBase] = None,
        prompt_template_config: Optional[PromptTemplateConfig] = None,
        prompt_execution_settings: Optional[
            Union[PromptExecutionSettings, List[PromptExecutionSettings], Dict[str, PromptExecutionSettings]]
        ] = None,
    ) -> None:
        """
        Initializes a new instance of the KernelFunctionFromPrompt class

        Args:
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            description (str): The description for the function

            prompt (Optional[str]): The prompt
            template_format (Optional[str]): The template format, default is "semantic-kernel"
            prompt_template (Optional[KernelPromptTemplate]): The prompt template
            prompt_template_config (Optional[PromptTemplateConfig]): The prompt template configuration
            prompt_execution_settings (Optional): instance, list or dict of PromptExecutionSettings to be used
                by the function, can also be supplied through prompt_template_config,
                but the supplied one is used if both are present.
                prompt_template_config (Optional[PromptTemplateConfig]): the prompt template config.
        """
        if not prompt and not prompt_template_config and not prompt_template:
            raise FunctionInitializationError(
                "The prompt cannot be empty, must be supplied directly, \
through prompt_template_config or in the prompt_template."
            )

        if not prompt_template:
            if not prompt_template_config:
                # prompt must be there if prompt_template and prompt_template_config is not supplied
                prompt_template_config = PromptTemplateConfig(
                    name=function_name,
                    description=description,
                    template=prompt,
                    template_format=template_format,
                )
            prompt_template = TEMPLATE_FORMAT_MAP[template_format](prompt_template_config=prompt_template_config)

        try:
            metadata = KernelFunctionMetadata(
                name=function_name,
                plugin_name=plugin_name,
                description=description,
                parameters=prompt_template.prompt_template_config.get_kernel_parameter_metadata(),
                is_prompt=True,
                is_asynchronous=True,
                return_parameter=PROMPT_RETURN_PARAM,
            )
        except ValidationError as exc:
            raise FunctionInitializationError("Failed to create KernelFunctionMetadata") from exc
        super().__init__(
            metadata=metadata, prompt_template=prompt_template, prompt_execution_settings=prompt_execution_settings
        )

    @model_validator(mode="before")
    @classmethod
    def rewrite_execution_settings(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, PromptExecutionSettings]:
        """Rewrite execution settings to a dictionary.

        If the prompt_execution_settings is not a dictionary, it is converted to a dictionary.
        If it is not supplied, but prompt_template is, the prompt_template's execution settings are used.
        """
        prompt_execution_settings = data.get("prompt_execution_settings")
        prompt_template = data.get("prompt_template")
        if not prompt_execution_settings:
            if prompt_template:
                prompt_execution_settings = prompt_template.prompt_template_config.execution_settings
                data["prompt_execution_settings"] = prompt_execution_settings
            if not prompt_execution_settings:
                return data
        if isinstance(prompt_execution_settings, PromptExecutionSettings):
            data["prompt_execution_settings"] = {
                prompt_execution_settings.service_id or "default": prompt_execution_settings
            }
        if isinstance(prompt_execution_settings, list):
            data["prompt_execution_settings"] = {s.service_id or "default": s for s in prompt_execution_settings}
        return data

    async def _invoke_internal(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> "FunctionResult":
        """Invokes the function with the given arguments."""
        arguments = self.add_default_values(arguments)
        service, execution_settings = kernel.select_ai_service(self, arguments)
        prompt = await self.prompt_template.render(kernel, arguments)

        if isinstance(service, ChatCompletionClientBase):
            return await self._handle_complete_chat(
                kernel=kernel,
                service=service,
                execution_settings=execution_settings,
                prompt=prompt,
                arguments=arguments,
            )

        if isinstance(service, TextCompletionClientBase):
            return await self._handle_text_complete(
                service=service,
                execution_settings=execution_settings,
                prompt=prompt,
                arguments=arguments,
            )

        raise ValueError(f"Service `{type(service).__name__}` is not a valid AI service")

    async def _handle_complete_chat(
        self,
        kernel: "Kernel",
        service: ChatCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        prompt: str,
        arguments: KernelArguments,
    ) -> FunctionResult:
        """Handles the chat service call."""
        chat_history = ChatHistory.from_rendered_prompt(prompt, service.get_chat_message_content_class())

        # pass the kernel in for auto function calling
        kwargs = {}
        if isinstance(execution_settings, OpenAIChatPromptExecutionSettings) and isinstance(
            service, ChatCompletionClientBase
        ):
            kwargs["kernel"] = kernel
            kwargs["arguments"] = arguments

        try:
            completions = await service.complete_chat(
                chat_history=chat_history,
                settings=execution_settings,
                **kwargs,
            )
            if not completions:
                raise FunctionExecutionException(f"No completions returned while invoking function {self.name}")

            return self._create_function_result(completions, chat_history, arguments)
        except Exception as exc:
            raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

    async def _handle_text_complete(
        self,
        service: TextCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        prompt: str,
        arguments: KernelArguments,
    ) -> FunctionResult:
        """Handles the text service call."""
        try:
            completions = await service.complete(prompt, execution_settings)
            return self._create_function_result(completions, None, arguments, prompt=prompt)
        except Exception as exc:
            raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

    def _create_function_result(
        self,
        completions: Union[List[ChatMessageContent], List[TextContent]],
        chat_history: ChatHistory,
        arguments: KernelArguments,
        prompt: str = None,
    ) -> FunctionResult:
        """Creates a function result with the given completions."""
        metadata = {
            "arguments": arguments,
            "metadata": [completion.metadata for completion in completions],
        }
        if chat_history:
            metadata["messages"] = chat_history
        if prompt:
            metadata["prompt"] = prompt
        return FunctionResult(
            function=self.metadata,
            value=completions,
            metadata=metadata,
        )

    async def _invoke_internal_stream(
        self,
        kernel: "Kernel",
        arguments: KernelArguments,
    ) -> AsyncIterable[Union[FunctionResult, List[StreamingKernelContent]]]:
        """Invokes the function stream with the given arguments."""
        arguments = self.add_default_values(arguments)
        service, execution_settings = kernel.select_ai_service(self, arguments)
        prompt = await self.prompt_template.render(kernel, arguments)

        if isinstance(service, ChatCompletionClientBase):
            async for content in self._handle_complete_chat_stream(
                kernel=kernel,
                service=service,
                execution_settings=execution_settings,
                prompt=prompt,
                arguments=arguments,
            ):
                yield content
            return

        if isinstance(service, TextCompletionClientBase):
            async for content in self._handle_complete_text_stream(
                service=service,
                execution_settings=execution_settings,
                prompt=prompt,
            ):
                yield content
            return

        raise FunctionExecutionException(f"Service `{type(service)}` is not a valid AI service")  # pragma: no cover

    async def _handle_complete_chat_stream(
        self,
        kernel: "Kernel",
        service: ChatCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        prompt: str,
        arguments: KernelArguments,
    ) -> AsyncIterable[Union[FunctionResult, List[StreamingKernelContent]]]:
        """Handles the chat service call."""

        # pass the kernel in for auto function calling
        kwargs = {}
        if isinstance(execution_settings, OpenAIChatPromptExecutionSettings) and isinstance(
            service, ChatCompletionClientBase
        ):
            kwargs["kernel"] = kernel
            kwargs["arguments"] = arguments

        chat_history = ChatHistory.from_rendered_prompt(prompt, service.get_chat_message_content_class())
        try:
            async for partial_content in service.complete_chat_stream(
                chat_history=chat_history,
                settings=execution_settings,
                **kwargs,
            ):
                yield partial_content

            return  # Exit after processing all iterations
        except Exception as e:
            logger.error(f"Error occurred while invoking function {self.name}: {e}")
            yield FunctionResult(function=self.metadata, value=None, metadata={"exception": e})

    async def _handle_complete_text_stream(
        self,
        service: TextCompletionClientBase,
        execution_settings: PromptExecutionSettings,
        prompt: str,
    ) -> AsyncIterable[Union[FunctionResult, List[StreamingKernelContent]]]:
        """Handles the text service call."""
        try:
            async for partial_content in service.complete_stream(prompt=prompt, settings=execution_settings):
                yield partial_content
            return
        except Exception as e:
            logger.error(f"Error occurred while invoking function {self.name}: {e}")
            yield FunctionResult(function=self.metadata, value=None, metadata={"exception": e})

    def add_default_values(self, arguments: "KernelArguments") -> KernelArguments:
        """Gathers the function parameters from the arguments."""
        for parameter in self.prompt_template.prompt_template_config.input_variables:
            if parameter.name not in arguments and parameter.default not in {None, "", False, 0}:
                arguments[parameter.name] = parameter.default
        return arguments
