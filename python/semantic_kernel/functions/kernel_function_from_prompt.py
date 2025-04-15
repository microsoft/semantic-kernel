# Copyright (c) Microsoft. All rights reserved.

import logging
import os
from collections.abc import AsyncGenerator, Mapping, Sequence
from html import unescape
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import Field, ValidationError, model_validator

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.connectors.ai.text_to_audio_client_base import TextToAudioClientBase
from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import FunctionExecutionException, FunctionInitializationError
from semantic_kernel.exceptions.function_exceptions import PromptRenderingException
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.filters.kernel_filters_extension import _rebuild_prompt_render_context
from semantic_kernel.filters.prompts.prompt_render_context import PromptRenderContext
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP, KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.prompt_rendering_result import PromptRenderingResult
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME, TEMPLATE_FORMAT_TYPES
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

logger: logging.Logger = logging.getLogger(__name__)

PROMPT_FILE_NAME = "skprompt.txt"
CONFIG_FILE_NAME = "config.json"
PROMPT_RETURN_PARAM = KernelParameterMetadata(
    name="return",
    description="The completion result",
    default_value=None,
    type="FunctionResult",  # type: ignore
    is_required=True,
)


class KernelFunctionFromPrompt(KernelFunction):
    """Semantic Kernel Function from a prompt."""

    prompt_template: PromptTemplateBase
    prompt_execution_settings: dict[str, PromptExecutionSettings] = Field(default_factory=dict)

    def __init__(
        self,
        function_name: str,
        plugin_name: str | None = None,
        description: str | None = None,
        prompt: str | None = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: PromptTemplateBase | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        prompt_execution_settings: PromptExecutionSettings
        | Sequence[PromptExecutionSettings]
        | Mapping[str, PromptExecutionSettings]
        | None = None,
    ) -> None:
        """Initializes a new instance of the KernelFunctionFromPrompt class.

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

        if prompt and prompt_template_config and prompt_template_config.template != prompt:
            logger.warning(
                f"Prompt ({prompt}) and PromptTemplateConfig ({prompt_template_config.template}) both supplied, "
                "using the template in PromptTemplateConfig, ignoring prompt."
            )
        if template_format and prompt_template_config and prompt_template_config.template_format != template_format:
            logger.warning(
                f"Template ({template_format}) and PromptTemplateConfig ({prompt_template_config.template_format}) "
                "both supplied, using the template format in PromptTemplateConfig, ignoring template."
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
            prompt_template = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](
                prompt_template_config=prompt_template_config
            )  # type: ignore

        try:
            metadata = KernelFunctionMetadata(
                name=function_name,
                plugin_name=plugin_name,
                description=description,
                parameters=prompt_template.prompt_template_config.get_kernel_parameter_metadata(),  # type: ignore
                is_prompt=True,
                is_asynchronous=True,
                return_parameter=PROMPT_RETURN_PARAM,
            )
        except ValidationError as exc:
            raise FunctionInitializationError("Failed to create KernelFunctionMetadata") from exc
        super().__init__(
            metadata=metadata,
            prompt_template=prompt_template,  # type: ignore
            prompt_execution_settings=prompt_execution_settings or {},  # type: ignore
        )

    @model_validator(mode="before")
    @classmethod
    def rewrite_execution_settings(
        cls,
        data: Any,
    ) -> dict[str, PromptExecutionSettings]:
        """Rewrite execution settings to a dictionary.

        If the prompt_execution_settings is not a dictionary, it is converted to a dictionary.
        If it is not supplied, but prompt_template is, the prompt_template's execution settings are used.
        """
        if isinstance(data, dict):
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
                    prompt_execution_settings.service_id or DEFAULT_SERVICE_NAME: prompt_execution_settings
                }
            if isinstance(prompt_execution_settings, Sequence):
                data["prompt_execution_settings"] = {
                    s.service_id or DEFAULT_SERVICE_NAME: s for s in prompt_execution_settings
                }
        return data

    async def _invoke_internal(self, context: FunctionInvocationContext) -> None:
        """Invokes the function with the given arguments."""
        prompt_render_result = await self._render_prompt(context)
        if prompt_render_result.function_result is not None:
            context.result = prompt_render_result.function_result
            return

        if isinstance(prompt_render_result.ai_service, ChatCompletionClientBase):
            chat_history = ChatHistory.from_rendered_prompt(prompt_render_result.rendered_prompt)
            try:
                chat_message_contents = await prompt_render_result.ai_service.get_chat_message_contents(
                    chat_history=chat_history,
                    settings=prompt_render_result.execution_settings,
                    **{"kernel": context.kernel, "arguments": context.arguments},
                )
            except Exception as exc:
                raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

            if not chat_message_contents:
                raise FunctionExecutionException(f"No completions returned while invoking function {self.name}")

            context.result = self._create_function_result(
                completions=chat_message_contents,
                chat_history=chat_history,
                arguments=context.arguments,
                prompt=prompt_render_result.rendered_prompt,
            )
            return

        if isinstance(prompt_render_result.ai_service, TextCompletionClientBase):
            try:
                texts = await prompt_render_result.ai_service.get_text_contents(
                    prompt=unescape(prompt_render_result.rendered_prompt),
                    settings=prompt_render_result.execution_settings,
                )
            except Exception as exc:
                raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

            context.result = self._create_function_result(
                completions=texts, arguments=context.arguments, prompt=prompt_render_result.rendered_prompt
            )
            return

        if isinstance(prompt_render_result.ai_service, TextToImageClientBase):
            try:
                images = await prompt_render_result.ai_service.get_image_content(
                    description=unescape(prompt_render_result.rendered_prompt),
                    settings=prompt_render_result.execution_settings,
                )
            except Exception as exc:
                raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

            context.result = self._create_function_result(
                completions=[images], arguments=context.arguments, prompt=prompt_render_result.rendered_prompt
            )
            return

        if isinstance(prompt_render_result.ai_service, TextToAudioClientBase):
            try:
                audio = await prompt_render_result.ai_service.get_audio_content(
                    text=unescape(prompt_render_result.rendered_prompt),
                    settings=prompt_render_result.execution_settings,
                )
            except Exception as exc:
                raise FunctionExecutionException(f"Error occurred while invoking function {self.name}: {exc}") from exc

            context.result = self._create_function_result(
                completions=[audio], arguments=context.arguments, prompt=prompt_render_result.rendered_prompt
            )
            return

        raise ValueError(f"Service `{type(prompt_render_result.ai_service).__name__}` is not a valid AI service")

    async def _invoke_internal_stream(self, context: FunctionInvocationContext) -> None:
        """Invokes the function stream with the given arguments."""
        prompt_render_result = await self._render_prompt(context, is_streaming=True)
        if prompt_render_result.function_result is not None:
            context.result = prompt_render_result.function_result
            return

        if isinstance(prompt_render_result.ai_service, ChatCompletionClientBase):
            chat_history = ChatHistory.from_rendered_prompt(prompt_render_result.rendered_prompt)
            value: AsyncGenerator = prompt_render_result.ai_service.get_streaming_chat_message_contents(
                chat_history=chat_history,
                settings=prompt_render_result.execution_settings,
                **{"kernel": context.kernel, "arguments": context.arguments},
            )
        elif isinstance(prompt_render_result.ai_service, TextCompletionClientBase):
            value = prompt_render_result.ai_service.get_streaming_text_contents(
                prompt=prompt_render_result.rendered_prompt, settings=prompt_render_result.execution_settings
            )
        else:
            raise FunctionExecutionException(
                f"Service `{type(prompt_render_result.ai_service)}` is not a valid AI service"
            )

        context.result = FunctionResult(
            function=self.metadata, value=value, rendered_prompt=prompt_render_result.rendered_prompt
        )

    async def _render_prompt(
        self, context: FunctionInvocationContext, is_streaming: bool = False
    ) -> PromptRenderingResult:
        """Render the prompt and apply the prompt rendering filters."""
        self.update_arguments_with_defaults(context.arguments)

        _rebuild_prompt_render_context()
        prompt_render_context = PromptRenderContext(
            function=self, kernel=context.kernel, arguments=context.arguments, is_streaming=is_streaming
        )

        stack = context.kernel.construct_call_stack(
            filter_type=FilterTypes.PROMPT_RENDERING,
            inner_function=self._inner_render_prompt,
        )
        await stack(prompt_render_context)

        if prompt_render_context.rendered_prompt is None:
            raise PromptRenderingException("Prompt rendering failed, no rendered prompt was returned.")
        selected_service: tuple["AIServiceClientBase", PromptExecutionSettings] = context.kernel.select_ai_service(
            function=self,
            arguments=context.arguments,
            type=(TextCompletionClientBase, ChatCompletionClientBase) if prompt_render_context.is_streaming else None,
        )
        return PromptRenderingResult(
            rendered_prompt=prompt_render_context.rendered_prompt,
            ai_service=selected_service[0],
            execution_settings=selected_service[1],
            function_result=prompt_render_context.function_result,
        )

    async def _inner_render_prompt(self, context: PromptRenderContext) -> None:
        """Render the prompt using the prompt template."""
        context.rendered_prompt = await self.prompt_template.render(context.kernel, context.arguments)

    def _create_function_result(
        self,
        completions: list[ChatMessageContent] | list[TextContent] | list[ImageContent] | list[AudioContent],
        arguments: KernelArguments,
        chat_history: ChatHistory | None = None,
        prompt: str | None = None,
    ) -> FunctionResult:
        """Creates a function result with the given completions."""
        metadata: dict[str, Any] = {
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
            rendered_prompt=prompt,
        )

    def update_arguments_with_defaults(self, arguments: KernelArguments) -> None:
        """Update any missing values with their defaults."""
        for parameter in self.prompt_template.prompt_template_config.input_variables:
            if parameter.name not in arguments and parameter.default not in {None, "", False, 0}:
                arguments[parameter.name] = parameter.default

    @classmethod
    def from_yaml(cls, yaml_str: str, plugin_name: str | None = None) -> "KernelFunctionFromPrompt":
        """Creates a new instance of the KernelFunctionFromPrompt class from a YAML string."""
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:  # pragma: no cover
            raise FunctionInitializationError(f"Invalid YAML content: {yaml_str}, error: {exc}") from exc

        if not isinstance(data, dict):
            raise FunctionInitializationError(f"The YAML content must represent a dictionary, got {yaml_str}")

        try:
            prompt_template_config = PromptTemplateConfig(**data)
        except ValidationError as exc:
            raise FunctionInitializationError(
                f"Error initializing PromptTemplateConfig: {exc} from yaml data: {data}"
            ) from exc
        return cls(
            function_name=prompt_template_config.name,
            plugin_name=plugin_name,
            description=prompt_template_config.description,
            prompt_template_config=prompt_template_config,
            template_format=prompt_template_config.template_format,
        )

    @classmethod
    def from_directory(cls, path: str, plugin_name: str | None = None) -> "KernelFunctionFromPrompt":
        """Creates a new instance of the KernelFunctionFromPrompt class from a directory.

        The directory needs to contain:
        - A prompt file named `skprompt.txt`
        - A config file named `config.json`

        Returns:
            KernelFunctionFromPrompt: The kernel function from prompt
        """
        prompt_path = os.path.join(path, PROMPT_FILE_NAME)
        config_path = os.path.join(path, CONFIG_FILE_NAME)
        prompt_exists = os.path.exists(prompt_path)
        config_exists = os.path.exists(config_path)
        if not config_exists and not prompt_exists:
            raise FunctionInitializationError(
                f"{PROMPT_FILE_NAME} and {CONFIG_FILE_NAME} files are required to create a "
                f"function from a directory, path: {path!s}."
            )
        if not config_exists:
            raise FunctionInitializationError(
                f"{CONFIG_FILE_NAME} files are required to create a function from a directory, "
                f"path: {path!s}, prompt file is there."
            )
        if not prompt_exists:
            raise FunctionInitializationError(
                f"{PROMPT_FILE_NAME} files are required to create a function from a directory, "
                f"path: {path!s}, config file is there."
            )

        function_name = os.path.basename(path)

        with open(config_path) as config_file:
            prompt_template_config = PromptTemplateConfig.from_json(config_file.read())
        prompt_template_config.name = function_name

        with open(prompt_path) as prompt_file:
            prompt_template_config.template = prompt_file.read()

        prompt_template = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](  # type: ignore
            prompt_template_config=prompt_template_config
        )
        return cls(
            function_name=function_name,
            plugin_name=plugin_name,
            prompt_template=prompt_template,
            prompt_template_config=prompt_template_config,
            template_format=prompt_template_config.template_format,
            description=prompt_template_config.description,
        )
