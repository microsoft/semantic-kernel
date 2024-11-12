# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai import AsyncStream
from openai.types import Completion as TextCompletion
from openai.types import CompletionChoice as TextCompletionChoice
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion import Choice as ChatCompletionChoice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChatCompletionChunkChoice

from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_streaming_text_completion,
    trace_text_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletionBase(OpenAIHandler, TextCompletionClientBase):
    """Base class for OpenAI text completion services."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OpenAITextPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        return str(self.client.base_url)

    @override
    @trace_text_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list["TextContent"]:
        if not isinstance(settings, (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings)):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings))  # nosec

        if isinstance(settings, OpenAITextPromptExecutionSettings):
            settings.prompt = prompt
        else:
            settings.messages = [{"role": "user", "content": prompt}]

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(settings)
        assert isinstance(response, (TextCompletion, ChatCompletion))  # nosec

        metadata = self._get_metadata_from_text_response(response)
        return [self._create_text_content(response, choice, metadata) for choice in response.choices]

    @override
    @trace_streaming_text_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        if not isinstance(settings, (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings)):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings))  # nosec

        if isinstance(settings, OpenAITextPromptExecutionSettings):
            settings.prompt = prompt
        else:
            if not settings.messages:
                settings.messages = [{"role": "user", "content": prompt}]
            else:
                settings.messages.append({"role": "user", "content": prompt})

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.stream = True

        response = await self._send_request(settings)
        assert isinstance(response, AsyncStream)  # nosec

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            assert isinstance(chunk, (TextCompletion, ChatCompletionChunk))  # nosec
            chunk_metadata = self._get_metadata_from_text_response(chunk)
            yield [self._create_streaming_text_content(chunk, choice, chunk_metadata) for choice in chunk.choices]

    # endregion

    def _create_text_content(
        self,
        response: TextCompletion | ChatCompletion,
        choice: TextCompletionChoice | ChatCompletionChoice,
        response_metadata: dict[str, Any],
    ) -> "TextContent":
        """Create a text content object from a choice."""
        choice_metadata = self._get_metadata_from_text_choice(choice)
        choice_metadata.update(response_metadata)
        text = choice.text if isinstance(choice, TextCompletionChoice) else choice.message.content
        return TextContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            text=text or "",
            metadata=choice_metadata,
        )

    def _create_streaming_text_content(
        self,
        chunk: TextCompletion | ChatCompletionChunk,
        choice: TextCompletionChoice | ChatCompletionChunkChoice,
        response_metadata: dict[str, Any],
    ) -> "StreamingTextContent":
        """Create a streaming text content object from a choice."""
        choice_metadata = self._get_metadata_from_text_choice(choice)
        choice_metadata.update(response_metadata)
        text = choice.text if isinstance(choice, TextCompletionChoice) else choice.delta.content
        return StreamingTextContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=choice_metadata,
            text=text or "",
        )

    def _get_metadata_from_text_response(
        self, response: TextCompletion | ChatCompletion | ChatCompletionChunk
    ) -> dict[str, Any]:
        """Get metadata from a response."""
        ret = {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }
        if response.usage is not None:
            ret["usage"] = CompletionUsage.from_openai(response.usage)
        return ret

    def _get_metadata_from_text_choice(
        self, choice: TextCompletionChoice | ChatCompletionChoice | ChatCompletionChunkChoice
    ) -> dict[str, Any]:
        """Get metadata from a completion choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }
