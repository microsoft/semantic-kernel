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
from semantic_kernel.connectors.ai.onnx.utils import ONNXTemplate, apply_template
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
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class OnnxGenAIChatCompletion(ChatCompletionClientBase, OnnxGenAICompletionBase):
    """OnnxGenAI text completion service."""

    template: ONNXTemplate
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    def __init__(
        self,
        template: ONNXTemplate,
        ai_model_path: str | None = None,
        ai_model_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes a new instance of the OnnxGenAITextCompletion class.

        Args:
            template : The chat template configuration.
            ai_model_path : Local path to the ONNX model Folder.
            ai_model_id : The ID of the AI model. Defaults to None.
            env_file_path : Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding : The encoding of the environment settings file.
            kwargs : Additional arguments.
        """
        try:
            settings = OnnxGenAISettings(
                chat_model_folder=ai_model_path,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Error creating OnnxGenAISettings: {e}") from e

        if settings.chat_model_folder is None:
            raise ServiceInitializationError(
                "AI model path is not provided. Please provide the 'ai_model_path' parameter in the constructor. "
                "OR set the 'ONNX_GEN_AI_CHAT_MODEL_FOLDER' environment variable."
            )

        if ai_model_id is None:
            ai_model_id = settings.chat_model_folder

        super().__init__(ai_model_id=ai_model_id, ai_model_path=settings.chat_model_folder, template=template, **kwargs)

    @override
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        """Create chat message contents, in the number specified by the settings.

        Args:
            chat_history : A list of chats in a chat_history object, that can be
                rendered into messages from system, user, assistant and tools.
            settings : Settings for the request.

        Returns:
            A list of chat message contents representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxGenAIPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxGenAIPromptExecutionSettings)  # nosec
        prompt = self._prepare_chat_history_for_request(chat_history)
        images = self._get_images_from_history(chat_history)
        choices = await self._generate_next_token(prompt, settings, images)
        return [self._create_chat_message_content(choice) for choice in choices]

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Create streaming chat message contents, in the number specified by the settings.

        Args:
            chat_history : A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings : Settings for the request.
            function_invoke_attempt : The function invoke attempt.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        if not isinstance(settings, OnnxGenAIPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OnnxGenAIPromptExecutionSettings)  # nosec
        prompt = self._prepare_chat_history_for_request(chat_history)
        images = self._get_images_from_history(chat_history)
        async for chunk in self._generate_next_token_async(prompt, settings, images):
            yield [
                self._create_streaming_chat_message_content(choice_index, new_token, function_invoke_attempt)
                for choice_index, new_token in enumerate(chunk)
            ]

    def _create_chat_message_content(self, choice: str) -> ChatMessageContent:
        return ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[
                TextContent(
                    text=choice,
                    ai_model_id=self.ai_model_id,
                )
            ],
        )

    def _create_streaming_chat_message_content(
        self, choice_index: int, choice: str, function_invoke_attempt: int
    ) -> StreamingChatMessageContent:
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=choice_index,
            content=choice,
            ai_model_id=self.ai_model_id,
            function_invoke_attempt=function_invoke_attempt,
        )

    @override
    def _prepare_chat_history_for_request(
        self, chat_history: ChatHistory, role_key: str = "role", content_key: str = "content"
    ) -> Any:
        return apply_template(chat_history, self.template)

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
