# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator, AsyncIterable
from functools import reduce
from typing import Any

import vertexai
from google.cloud.aiplatform_v1beta1.types.content import Content
from pydantic import ValidationError
from vertexai.generative_models import Candidate, GenerationResponse, GenerativeModel

from semantic_kernel.connectors.ai.google.shared_utils import (
    configure_function_choice_behavior,
    filter_system_message,
    format_gemini_function_name_to_kernel_function_fully_qualified_name,
    invoke_function_calls,
)
from semantic_kernel.connectors.ai.google.vertex_ai.services.utils import (
    finish_reason_from_vertex_ai_to_semantic_kernel,
    format_assistant_message,
    format_tool_message,
    format_user_message,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_base import VertexAIBase
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.kernel import Kernel

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase


class VertexAIChatCompletion(VertexAIBase, ChatCompletionClientBase):
    """Google Vertex AI Chat Completion Service."""

    def __init__(
        self,
        project_id: str | None = None,
        region: str | None = None,
        gemini_model_id: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google Vertex AI Chat Completion Service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - VERTEX_AI_GEMINI_MODEL_ID
        - VERTEX_AI_PROJECT_ID
        - VERTEX_AI_REGION

        Args:
            project_id (str): The Google Cloud project ID.
            region (str): The Google Cloud region.
            gemini_model_id (str): The Gemini model ID.
            service_id (str): The Vertex AI service ID.
            env_file_path (str): The path to the environment file.
            env_file_encoding (str): The encoding of the environment file.
        """
        try:
            vertex_ai_settings = VertexAISettings.create(
                project_id=project_id,
                region=region,
                gemini_model_id=gemini_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Vertex AI settings: {e}") from e
        if not vertex_ai_settings.gemini_model_id:
            raise ServiceInitializationError("The Vertex AI Gemini model ID is required.")

        super().__init__(
            ai_model_id=vertex_ai_settings.gemini_model_id,
            service_id=service_id or vertex_ai_settings.gemini_model_id,
            service_settings=vertex_ai_settings,
        )

    # region Non-streaming
    @override
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VertexAIChatPromptExecutionSettings)  # nosec

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(chat_history, settings)

        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")

        configure_function_choice_behavior(settings, kernel, update_settings_from_function_choice_configuration)

        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(chat_history, settings)
            chat_history.add_message(message=completions[0])
            function_calls = [item for item in chat_history.messages[-1].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions

            results = await invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=kwargs.get("arguments", None),
                function_call_count=fc_count,
                request_index=request_index,
                function_behavior=settings.function_choice_behavior,
            )

            if any(result.terminate for result in results if result is not None):
                return completions
        else:
            # do a final call without auto function calling
            return await self._send_chat_request(chat_history, settings)

    async def _send_chat_request(
        self, chat_history: ChatHistory, settings: VertexAIChatPromptExecutionSettings
    ) -> list[ChatMessageContent]:
        """Send a chat request to the Vertex AI service."""
        vertexai.init(project=self.service_settings.project_id, location=self.service_settings.region)
        model = GenerativeModel(
            self.service_settings.gemini_model_id,
            system_instruction=filter_system_message(chat_history),
        )

        response: GenerationResponse = await model.generate_content_async(
            contents=self._prepare_chat_history_for_request(chat_history),
            generation_config=settings.prepare_settings_dict(),
            tools=settings.tools,
            tool_config=settings.tool_config,
        )

        return [self._create_chat_message_content(response, candidate) for candidate in response.candidates]

    def _create_chat_message_content(self, response: GenerationResponse, candidate: Candidate) -> ChatMessageContent:
        """Create a chat message content object.

        Args:
            response: The response from the service.
            candidate: The candidate from the response.

        Returns:
            A chat message content object.
        """
        # Best effort conversion of finish reason. The raw value will be available in metadata.
        finish_reason: FinishReason | None = finish_reason_from_vertex_ai_to_semantic_kernel(candidate.finish_reason)
        response_metadata = self._get_metadata_from_response(response)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        items: list[ITEM_TYPES] = []
        for idx, part in enumerate(candidate.content.parts):
            part_dict = part.to_dict()
            if "text" in part_dict:
                items.append(TextContent(text=part.text, inner_content=response, metadata=response_metadata))
            elif "function_call" in part_dict:
                items.append(
                    FunctionCallContent(
                        id=f"{part.function_call.name}_{idx!s}",
                        name=format_gemini_function_name_to_kernel_function_fully_qualified_name(
                            part.function_call.name
                        ),
                        arguments={k: v for k, v in part.function_call.args.items()},
                    )
                )

        return ChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            finish_reason=finish_reason,
            metadata=response_metadata,
        )

    # endregion

    # region Streaming
    @override
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VertexAIChatPromptExecutionSettings)  # nosec

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            # No auto invoke is required.
            async_generator = self._send_chat_streaming_request(chat_history, settings)
        else:
            # Auto invoke is required.
            async_generator = self._get_streaming_chat_message_contents_auto_invoke(chat_history, settings, **kwargs)

        async for messages in async_generator:
            yield messages

    async def _get_streaming_chat_message_contents_auto_invoke(
        self,
        chat_history: ChatHistory,
        settings: VertexAIChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Get streaming chat message contents from the Google AI service with auto invoking functions."""
        kernel = kwargs.get("kernel")
        if not isinstance(kernel, Kernel):
            raise ServiceInvalidExecutionSettingsError("Kernel is required for auto invoking functions.")
        if not settings.function_choice_behavior:
            raise ServiceInvalidExecutionSettingsError(
                "Function choice behavior is required for auto invoking functions."
            )

        configure_function_choice_behavior(settings, kernel, update_settings_from_function_choice_configuration)

        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_streaming_request(chat_history, settings):
                for message in messages:
                    if message:
                        all_messages.append(message)
                        if any(isinstance(item, FunctionCallContent) for item in message.items):
                            function_call_returned = True
                yield messages

            if not function_call_returned:
                # Response doesn't contain any function calls. No need to proceed to the next request.
                return

            full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_messages)
            function_calls = [item for item in full_completion.items if isinstance(item, FunctionCallContent)]
            chat_history.add_message(message=full_completion)

            results = await invoke_function_calls(
                function_calls=function_calls,
                chat_history=chat_history,
                kernel=kernel,
                arguments=kwargs.get("arguments", None),
                function_call_count=len(function_calls),
                request_index=request_index,
                function_behavior=settings.function_choice_behavior,
            )

            if any(result.terminate for result in results if result is not None):
                return

    async def _send_chat_streaming_request(
        self,
        chat_history: ChatHistory,
        settings: VertexAIChatPromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Send a streaming chat request to the Vertex AI service."""
        vertexai.init(project=self.service_settings.project_id, location=self.service_settings.region)
        model = GenerativeModel(
            self.service_settings.gemini_model_id,
            system_instruction=filter_system_message(chat_history),
        )

        response: AsyncIterable[GenerationResponse] = await model.generate_content_async(
            contents=self._prepare_chat_history_for_request(chat_history),
            generation_config=settings.prepare_settings_dict(),
            tools=settings.tools,
            tool_config=settings.tool_config,
            stream=True,
        )

        async for chunk in response:
            yield [self._create_streaming_chat_message_content(chunk, candidate) for candidate in chunk.candidates]

    def _create_streaming_chat_message_content(
        self,
        chunk: GenerationResponse,
        candidate: Candidate,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object.

        Args:
            chunk: The response from the service.
            candidate: The candidate from the response.

        Returns:
            A streaming chat message content object.
        """
        # Best effort conversion of finish reason. The raw value will be available in metadata.
        finish_reason: FinishReason | None = finish_reason_from_vertex_ai_to_semantic_kernel(candidate.finish_reason)
        response_metadata = self._get_metadata_from_response(chunk)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        items: list[STREAMING_ITEM_TYPES] = []
        for idx, part in enumerate(candidate.content.parts):
            part_dict = part.to_dict()
            if "text" in part_dict:
                items.append(
                    StreamingTextContent(
                        choice_index=candidate.index,
                        text=part.text,
                        inner_content=chunk,
                        metadata=response_metadata,
                    )
                )
            elif "function_call" in part_dict:
                items.append(
                    FunctionCallContent(
                        id=f"{part.function_call.name}_{idx!s}",
                        name=format_gemini_function_name_to_kernel_function_fully_qualified_name(
                            part.function_call.name
                        ),
                        arguments={k: v for k, v in part.function_call.args.items()},
                    )
                )

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            choice_index=candidate.index,
            items=items,
            inner_content=chunk,
            finish_reason=finish_reason,
            metadata=response_metadata,
        )

    # endregion

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[Content]:
        chat_request_messages: list[Content] = []

        for message in chat_history.messages:
            if message.role == AuthorRole.SYSTEM:
                # Skip system messages since they are not part of the chat request.
                # System message will be provided as system_instruction in the model.
                continue
            if message.role == AuthorRole.USER:
                chat_request_messages.append(Content(role="user", parts=format_user_message(message)))
            elif message.role == AuthorRole.ASSISTANT:
                chat_request_messages.append(Content(role="model", parts=format_assistant_message(message)))
            elif message.role == AuthorRole.TOOL:
                chat_request_messages.append(Content(role="function", parts=format_tool_message(message)))

        return chat_request_messages

    def _get_metadata_from_response(self, response: GenerationResponse) -> dict[str, Any]:
        """Get metadata from the response.

        Args:
            response: The response from the service.

        Returns:
            A dictionary containing metadata.
        """
        return {
            "prompt_feedback": response.prompt_feedback,
            "usage": response.usage_metadata,
        }

    def _get_metadata_from_candidate(self, candidate: Candidate) -> dict[str, Any]:
        """Get metadata from the candidate.

        Args:
            candidate: The candidate from the response.

        Returns:
            A dictionary containing metadata.
        """
        return {
            "index": candidate.index,
            "finish_reason": candidate.finish_reason,
            "safety_ratings": candidate.safety_ratings,
        }

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return VertexAIChatPromptExecutionSettings
