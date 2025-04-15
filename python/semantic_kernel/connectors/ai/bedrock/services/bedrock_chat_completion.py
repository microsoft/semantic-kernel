# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator, Callable
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from pydantic import ValidationError

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.bedrock_settings import BedrockSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_base import BedrockBase
from semantic_kernel.connectors.ai.bedrock.services.model_provider.bedrock_model_provider import (
    get_chat_completion_additional_model_request_fields,
)
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import (
    MESSAGE_CONVERTERS,
    finish_reason_from_bedrock_to_semantic_kernel,
    remove_none_recursively,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_chat_message_content import STREAMING_CMC_ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidRequestError,
    ServiceInvalidResponseError,
)
from semantic_kernel.utils.async_utils import run_in_executor
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory


class BedrockChatCompletion(BedrockBase, ChatCompletionClientBase):
    """Amazon Bedrock Chat Completion Service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    def __init__(
        self,
        model_id: str | None = None,
        service_id: str | None = None,
        runtime_client: Any | None = None,
        client: Any | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Amazon Bedrock Chat Completion Service.

        Args:
            model_id: The Amazon Bedrock chat model ID to use.
            service_id: The Service ID for the completion service.
            runtime_client: The Amazon Bedrock runtime client to use.
            client: The Amazon Bedrock client to use.
            env_file_path: The path to the .env file.
            env_file_encoding: The encoding of the .env file.
        """
        try:
            bedrock_settings = BedrockSettings(
                chat_model_id=model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError("Failed to initialize the Amazon Bedrock Chat Completion Service.") from e

        if bedrock_settings.chat_model_id is None:
            raise ServiceInitializationError("The Amazon Bedrock Chat Model ID is missing.")

        super().__init__(
            ai_model_id=bedrock_settings.chat_model_id,
            service_id=service_id or bedrock_settings.chat_model_id,
            runtime_client=runtime_client,
            client=client,
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

        prepared_settings = self._prepare_settings_for_request(chat_history, settings)
        response = await self._async_converse(**prepared_settings)

        return [self._create_chat_message_content(response)]

    @override
    @trace_streaming_chat_completion(BedrockBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        # Not all models support streaming: check if the model supports streaming before proceeding
        model_info = await self.get_foundation_model_info(self.ai_model_id)
        if not model_info.get("responseStreamingSupported"):
            raise ServiceInvalidRequestError(f"The model {self.ai_model_id} does not support streaming.")

        if not isinstance(settings, BedrockChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, BedrockChatPromptExecutionSettings)  # nosec

        prepared_settings = self._prepare_settings_for_request(chat_history, settings)
        response_stream = await self._async_converse_streaming(**prepared_settings)
        for event in response_stream.get("stream"):
            if "messageStart" in event:
                yield [self._parse_message_start_event(event)]
            elif "contentBlockStart" in event:
                yield [self._parse_content_block_start_event(event)]
            elif "contentBlockDelta" in event:
                yield [self._parse_content_block_delta_event(event, function_invoke_attempt)]
            elif "contentBlockStop" in event:
                continue
            elif "messageStop" in event:
                yield [self._parse_message_stop_event(event)]
            elif "metadata" in event:
                yield [self._parse_metadata_event(event)]
            else:
                raise ServiceInvalidResponseError(f"Unknown event type in the response: {event}")

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[["FunctionCallChoiceConfiguration", "PromptExecutionSettings", FunctionChoiceType], None]:
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
        chat_history: "ChatHistory",
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
            "additionalModelRequestFields": get_chat_completion_additional_model_request_fields(
                self.ai_model_id, settings
            ),
        }

        if settings.tools and settings.tool_choice:
            prepared_settings["toolConfig"] = {
                "tools": settings.tools,
                "toolChoice": settings.tool_choice,
            }

        return prepared_settings

    def _create_chat_message_content(self, response: dict[str, Any]) -> ChatMessageContent:
        """Create a chat message content object."""
        finish_reason: FinishReason | None = finish_reason_from_bedrock_to_semantic_kernel(response["stopReason"])
        usage = CompletionUsage(
            prompt_tokens=response["usage"]["inputTokens"],
            completion_tokens=response["usage"]["outputTokens"],
        )
        items: list[CMC_ITEM_TYPES] = []
        for content in response["output"]["message"]["content"]:
            if "text" in content:
                items.append(TextContent(text=content["text"], inner_content=content))
            elif "image" in content:
                items.append(
                    ImageContent(
                        data=content["image"]["source"]["bytes"],
                        mime_type=content["image"]["source"]["format"],
                        inner_content=content["image"],
                    )
                )
            elif "toolUse" in content:
                items.append(
                    FunctionCallContent(
                        id=content["toolUse"]["toolUseId"],
                        name=content["toolUse"]["name"],
                        arguments=content["toolUse"]["input"],
                    )
                )
            else:
                raise ServiceInvalidResponseError(f"Unsupported content type in the response: {content}")

        return ChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            finish_reason=finish_reason,
            metadata={"usage": usage},
        )

    # region async helper methods

    async def _async_converse(self, **kwargs) -> Any:
        """Invoke the model asynchronously."""
        return await run_in_executor(
            None,
            partial(
                self.bedrock_runtime_client.converse,
                **kwargs,
            ),
        )

    async def _async_converse_streaming(self, **kwargs) -> Any:
        """Invoke the model asynchronously."""
        return await run_in_executor(
            None,
            partial(
                self.bedrock_runtime_client.converse_stream,
                **kwargs,
            ),
        )

    # endregion

    # region streaming event parsing methods

    def _parse_message_start_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Parse the message start event.

        The message start event contains the role of the message.
        https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_MessageStartEvent.html
        """
        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole(event["messageStart"]["role"]),
            items=[],
            choice_index=0,
            inner_content=event,
        )

    def _parse_content_block_start_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Parse the content block start event.

        The content block start event contains tool information.
        https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ContentBlockStartEvent.html
        """
        items: list[STREAMING_ITEM_TYPES] = []
        if "toolUse" in event["contentBlockStart"]["start"]:
            items.append(
                FunctionCallContent(
                    id=event["contentBlockStart"]["start"]["toolUse"]["toolUseId"],
                    name=event["contentBlockStart"]["start"]["toolUse"]["name"],
                )
            )

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,  # Assume the role is always assistant
            items=items,
            choice_index=0,
            inner_content=event,
        )

    def _parse_content_block_delta_event(
        self, event: dict[str, Any], function_invoke_attempt: int
    ) -> StreamingChatMessageContent:
        """Parse the content block delta event.

        The content block delta event contains the completion.
        https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ContentBlockDeltaEvent.html
        """
        items: list[STREAMING_ITEM_TYPES] = [
            StreamingTextContent(
                choice_index=0,
                text=event["contentBlockDelta"]["delta"]["text"],
                inner_content=event,
            )
            if "text" in event["contentBlockDelta"]["delta"]
            else FunctionCallContent(
                arguments=event["contentBlockDelta"]["delta"]["toolUse"]["input"],
                inner_content=event,
            )
        ]

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,  # Assume the role is always assistant
            items=items,
            choice_index=0,
            inner_content=event,
            function_invoke_attempt=function_invoke_attempt,
        )

    def _parse_message_stop_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Parse the message stop event.

        The message stop event contains the finish reason.
        https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_MessageStopEvent.html
        """
        metadata = event["messageStop"].get("additionalModelResponseFields", {})

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,  # Assume the role is always assistant
            items=[],
            choice_index=0,
            inner_content=event,
            finish_reason=finish_reason_from_bedrock_to_semantic_kernel(event["messageStop"]["stopReason"]),
            metadata=metadata,
        )

    def _parse_metadata_event(self, event: dict[str, Any]) -> StreamingChatMessageContent:
        """Parse the metadata event.

        The metadata event contains additional information.
        https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ConverseStreamMetadataEvent.html
        """
        usage = CompletionUsage(
            prompt_tokens=event["metadata"]["usage"]["inputTokens"],
            completion_tokens=event["metadata"]["usage"]["outputTokens"],
        )

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,  # Assume the role is always assistant
            items=[],
            choice_index=0,
            inner_content=event,
            metadata={"usage": usage},
        )

    # endregion
