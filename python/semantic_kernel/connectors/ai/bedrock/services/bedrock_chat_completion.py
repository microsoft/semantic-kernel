# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator, Callable
from functools import partial
from typing import TYPE_CHECKING, Any

import boto3

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.bedrock_settings import BedrockSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_base import BedrockBase
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import (
    MESSAGE_CONVERTERS,
    remove_none_recursively,
    run_in_executor,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.contents.utils.author_role import AuthorRole
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

    def __init__(
        self,
        model_id: str | None = None,
        runtime_client: Any | None = None,
        client: Any | None = None,
    ) -> None:
        """Initialize the Amazon Bedrock Chat Completion Service.

        Args:
            model_id: The Amazon Bedrock chat model ID to use.
            runtime_client: The Amazon Bedrock runtime client to use.
            client: The Amazon Bedrock client to use.
        """
        try:
            bedrock_settings = BedrockSettings.create(chat_model_id=model_id)
        except ValidationError as e:
            raise ServiceInitializationError("Failed to initialize the Amazon Bedrock Chat Completion Service.") from e

        if bedrock_settings.chat_model_id is None:
            raise ServiceInitializationError("The Amazon Bedrock Chat Model ID is missing.")

        super().__init__(
            ai_model_id=bedrock_settings.chat_model_id,
            bedrock_runtime_client=runtime_client or boto3.client("bedrock-runtime"),
            bedrock_client=client or boto3.client("bedrock"),
        )

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

        response = await self._async_converse(**self._prepare_settings_for_request(chat_history, settings))

        return [self._create_chat_message_content(response)]

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

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_choice_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> Any:
        messages: list[dict[str, Any]] = []

        for message in chat_history.messages:
            if message.role == AuthorRole.SYSTEM:
                continue
            messages.append(MESSAGE_CONVERTERS[message.role](message))

        return messages

    # endregion

    def _prepare_system_messages_for_request(self, chat_history: "ChatHistory") -> Any:
        messages: list[dict[str, Any]] = []

        for message in chat_history.messages:
            if message.role != AuthorRole.SYSTEM:
                continue
            messages.append(MESSAGE_CONVERTERS[message.role](message))

        return messages

    def _prepare_settings_for_request(
        self,
        chat_history: ChatHistory,
        settings: "BedrockChatPromptExecutionSettings",
    ) -> dict[str, Any]:
        """Prepare the settings for the request.

        Settings are prepared based on the syntax shown here:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime/client/converse.html

        Note that Guardrails are not supported.
        """
        prepared_settings = {
            "modelId": self.ai_model_id,
            "messages": self._prepare_chat_history_for_request(chat_history),
            "system": self._prepare_system_messages_for_request(chat_history),
            "inferenceConfig": remove_none_recursively({
                "maxTokens": settings.max_tokens,
                "temperature": settings.temperature,
                "topP": settings.top_p,
                "stopSequences": settings.stop,
            }),
        }

        if settings.tools and settings.tool_choice:
            prepared_settings["toolConfig"] = {
                "tools": settings.tools,
                "toolChoice": settings.tool_choice,
            }

        return prepared_settings

    def _create_chat_message_content(self, response: dict[str, Any]) -> ChatMessageContent:
        """Create a chat message content object."""
        return ChatMessageContent(AuthorRole.ASSISTANT, [])

    async def _async_converse(self, **kwargs) -> Any:
        """Invoke the model asynchronously."""
        return await run_in_executor(
            None,
            partial(
                self.bedrock_runtime_client.converse,
                **kwargs,
            ),
        )
