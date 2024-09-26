# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.bedrock_settings import BedrockSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_base import BedrockBase
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


class BedrockChatCompletion(BedrockBase, ChatCompletionClientBase):
    """Amazon Bedrock Chat Completion Service."""

    def __init__(self, model_id: str | None = None, client: Any | None = None) -> None:
        """Initialize the Amazon Bedrock Chat Completion Service.

        Args:
            model_id: The Amazon Bedrock chat model ID to use.
            client: The Amazon Bedrock client to use.
        """
        try:
            bedrock_settings = BedrockSettings.create(chat_model_id=model_id)
        except ValidationError as e:
            raise ServiceInitializationError("Failed to initialize the Amazon Bedrock Chat Completion Service.") from e

        if bedrock_settings.chat_model_id is None:
            raise ServiceInitializationError("The Amazon Bedrock Chat Model ID is missing.")

        super().__init__(ai_model_id=bedrock_settings.chat_model_id, client=client)

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return BedrockChatPromptExecutionSettings

    @override
    @trace_chat_completion(BedrockBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, BedrockChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, BedrockChatPromptExecutionSettings)  # nosec

        return []

    @override
    @trace_streaming_chat_completion(BedrockBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, BedrockChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, BedrockChatPromptExecutionSettings)  # nosec

        yield []

    # endregion
