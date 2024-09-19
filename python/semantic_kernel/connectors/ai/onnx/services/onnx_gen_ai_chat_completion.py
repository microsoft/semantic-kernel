# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_prompt_execution_settings import OnnxGenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_settings import OnnxGenAISettings
from semantic_kernel.connectors.ai.onnx.services.onnx_gen_ai_completion_base import OnnxGenAICompletionBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import (
    ChatHistory,
    ChatMessageContent,
    ImageContent,
    StreamingChatMessageContent,
    TextContent,
)
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ServiceInitializationError, ServiceInvalidExecutionSettingsError
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP
from semantic_kernel.prompt_template import PromptTemplateConfig
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OnnxGenAIChatCompletion(ChatCompletionClientBase, OnnxGenAICompletionBase):
    """OnnxGenAI text completion service."""

    prompt_template: PromptTemplateConfig
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    def __init__(
        self,
        prompt_template: str | PromptTemplateConfig,
        ai_model_path: str | None = None,
        ai_model_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the OnnxGenAITextCompletion class.

        Args:
            ai_model_path (str): Local path to the ONNX model Folder.
            prompt_template (str | PromptTemplateConfig): The prompt template configuration.
                The template can either be a jinja template or a complete prompt template config.
            ai_model_id (str, optional): The ID of the AI model. Defaults to None.
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding (str | None): The encoding of the environment settings file.
        """
        try:
            settings = OnnxGenAISettings.create(
                model_path=ai_model_path,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Error creating OnnxGenAISettings: {e!s}") from e

        if ai_model_id is None:
            ai_model_id = settings.model_path

        if type(prompt_template) is str:
            prompt_template = PromptTemplateConfig(
                template=prompt_template,
                template_format="jinja2",
            )

        super().__init__(ai_model_id=ai_model_id, ai_model_path=settings.model_path, prompt_template=prompt_template)

    @override
    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Create chat message contents, in the number specified by the settings.

        Args:
            chat_history (ChatHistory): A list of chats in a chat_history object, that can be
                rendered into messages from system, user, assistant and tools.
            settings (PromptExecutionSettings): Settings for the request.
            **kwargs (Any): The optional arguments.

        Returns:
            A list of chat message contents representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxGenAIPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxGenAIPromptExecutionSettings)  # nosec
        prompt = await self._apply_chat_template(chat_history, **kwargs)
        images = self._get_images_from_history(chat_history)
        new_tokens = ""
        async for new_token in self._generate_next_token(prompt, settings, images):
            new_tokens += new_token

        model_answer = ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[
                TextContent(
                    text=new_tokens,
                    ai_model_id=self.ai_model_id,
                )
            ],
        )
        return [model_answer]

    @override
    async def get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Create streaming chat message contents, in the number specified by the settings.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxGenAIPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxGenAIPromptExecutionSettings)  # nosec
        prompt = await self._apply_chat_template(chat_history, **kwargs)
        images = self._get_images_from_history(chat_history)
        async for new_token in self._generate_next_token(prompt, settings, images):
            yield [
                StreamingChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    choice_index=0,
                    content=new_token,
                    ai_model_id=self.ai_model_id,
                )
            ]

    async def _apply_chat_template(self, chat_history: "ChatHistory", **kwargs) -> str:
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if kernel is None:
            raise ServiceInvalidExecutionSettingsError("The kernel is required for OnnxChatCompletion")
        if arguments is None:
            arguments = KernelArguments(messages=self._prepare_chat_history_for_request(chat_history))
            logger.warning("The arguments were not provided, auto injecting chat history as messages.")
        template = TEMPLATE_FORMAT_MAP[self.prompt_template.template_format](
            prompt_template_config=self.prompt_template
        )  # type: ignore
        return await template.render(kernel, arguments)

    def _get_images_from_history(self, chat_history: "ChatHistory") -> ImageContent | None:
        images = []
        for message in chat_history.messages:
            for image in message.items:
                if isinstance(image, ImageContent):
                    if not self.enable_multi_modality:
                        raise ServiceInvalidExecutionSettingsError("The model does not support multi-modality")
                    if image.uri:
                        images.append(image)
                    else:
                        raise ServiceInvalidExecutionSettingsError(
                            "Image Content URI needs to be set, because onnx can only work with file paths"
                        )
        # Currently Onnx Runtime only supports one image
        # Later we will add support for multiple images
        if len(images) > 1:
            raise ServiceInvalidExecutionSettingsError("The model does not support more than one image")
        return images[-1] if images else None

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return OnnxGenAIPromptExecutionSettings
