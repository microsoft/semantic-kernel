# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any, Dict, List

from openai import AsyncStream
from openai.types import Completion, CompletionChoice

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAITextRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.models.contents import StreamingTextContent, TextContent

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
        OpenAIRequestSettings,
    )

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletionBase(OpenAIHandler, TextCompletionClientBase):
    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return OpenAITextRequestSettings

    async def complete(
        self,
        prompt: str,
        settings: "OpenAIRequestSettings",
        **kwargs,
    ) -> List["TextContent"]:
        """Executes a completion request and returns the result.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAIRequestSettings} -- The settings to use for the completion request.

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        if isinstance(settings, OpenAITextRequestSettings):
            settings.prompt = prompt
        else:
            settings.messages = [{"role": "user", "content": prompt}]
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        metadata = self.get_metadata_from_text_response(response)
        return [self._create_return_content(response, choice, metadata) for choice in response.choices]

    def _create_return_content(
        self, response: Completion, choice: CompletionChoice, response_metadata: Dict[str, Any]
    ) -> "TextContent":
        """Create a text content object from a choice."""
        choice_metadata = self.get_metadata_from_text_choice(choice)
        choice_metadata.update(response_metadata)
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            text=choice.text,
            metadata=choice_metadata,
        )

    async def complete_stream(
        self,
        prompt: str,
        settings: "OpenAIRequestSettings",
        **kwargs,
    ) -> AsyncIterable[List["StreamingTextContent"]]:
        """
        Executes a completion request and streams the result.
        Supports both chat completion and text completion.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAIRequestSettings} -- The settings to use for the completion request.

        Returns:
            Union[str, List[str]] -- The completion result(s).
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
            raise ValueError("Expected an AsyncStream[Completion] response.")

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self.get_metadata_from_text_response(chunk)
            yield [self._create_return_content_stream(chunk, choice, chunk_metadata) for choice in chunk.choices]

    def _create_return_content_stream(
        self, chunk: Completion, choice: CompletionChoice, response_metadata: Dict[str, Any]
    ) -> "StreamingTextContent":
        """Create a text content object from a choice."""
        choice_metadata = self.get_metadata_from_text_choice(choice)
        choice_metadata.update(response_metadata)
        return StreamingTextContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=choice_metadata,
            text=choice.text,
        )

    def get_metadata_from_text_response(self, response: Completion) -> Dict[str, Any]:
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": response.usage,
        }

    def get_metadata_from_streaming_text_response(self, response: Completion) -> Dict[str, Any]:
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }

    def get_metadata_from_text_choice(self, choice: CompletionChoice) -> Dict[str, Any]:
        return {
            "logprobs": choice.logprobs,
        }
