# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, AsyncIterable, Dict, List, Union

from openai import AsyncStream
from openai.types import Completion, CompletionChoice
from openai.types.chat.chat_completion import Choice as ChatCompletionChoice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import StreamingTextContent, TextContent
from semantic_kernel.exceptions import ServiceInvalidResponseError

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
        OpenAIPromptExecutionSettings,
    )

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletionBase(OpenAIHandler, TextCompletionClientBase):
    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return OpenAITextPromptExecutionSettings

    async def complete(
        self,
        prompt: str,
        settings: "OpenAIPromptExecutionSettings",
    ) -> List["TextContent"]:
        """Executes a completion request and returns the result.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAITextPromptExecutionSettings} -- The settings to use for the completion request.

        Returns:
            List["TextContent"] -- The completion result(s).
        """
        if isinstance(settings, OpenAITextPromptExecutionSettings):
            settings.prompt = prompt
        else:
            settings.messages = [{"role": "user", "content": prompt}]
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        metadata = self._get_metadata_from_text_response(response)
        return [self._create_text_content(response, choice, metadata) for choice in response.choices]

    def _create_text_content(
        self,
        response: Completion,
        choice: Union[CompletionChoice, ChatCompletionChoice],
        response_metadata: Dict[str, Any],
    ) -> "TextContent":
        """Create a text content object from a choice."""
        choice_metadata = self._get_metadata_from_text_choice(choice)
        choice_metadata.update(response_metadata)
        text = choice.text if isinstance(choice, CompletionChoice) else choice.message.content
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            text=text,
            metadata=choice_metadata,
        )

    async def complete_stream(
        self,
        prompt: str,
        settings: "OpenAIPromptExecutionSettings",
    ) -> AsyncIterable[List["StreamingTextContent"]]:
        """
        Executes a completion request and streams the result.
        Supports both chat completion and text completion.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAITextPromptExecutionSettings} -- The settings to use for the completion request.

        Yields:
            List["StreamingTextContent"] -- The result stream made up of StreamingTextContent objects.
        """
        if "prompt" in settings.model_fields:
            settings.prompt = prompt
        if "messages" in settings.model_fields:
            if not settings.messages:
                settings.messages = [{"role": "user", "content": prompt}]
            else:
                settings.messages.append({"role": "user", "content": prompt})
        settings.ai_model_id = self.ai_model_id
        settings.stream = True
        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError("Expected an AsyncStream[Completion] response.")

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_text_response(chunk)
            yield [self._create_streaming_text_content(chunk, choice, chunk_metadata) for choice in chunk.choices]

    def _create_streaming_text_content(
        self, chunk: Completion, choice: Union[CompletionChoice, ChatCompletionChunk], response_metadata: Dict[str, Any]
    ) -> "StreamingTextContent":
        """Create a streaming text content object from a choice."""
        choice_metadata = self._get_metadata_from_text_choice(choice)
        choice_metadata.update(response_metadata)
        text = choice.text if isinstance(choice, CompletionChoice) else choice.delta.content
        return StreamingTextContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=choice_metadata,
            text=text,
        )

    def _get_metadata_from_text_response(self, response: Completion) -> Dict[str, Any]:
        """Get metadata from a completion response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": response.usage,
        }

    def _get_metadata_from_streaming_text_response(self, response: Completion) -> Dict[str, Any]:
        """Get metadata from a streaming completion response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }

    def _get_metadata_from_text_choice(self, choice: CompletionChoice) -> Dict[str, Any]:
        """Get metadata from a completion choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }
