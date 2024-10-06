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

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_text_completion
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_text_completion
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< main
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
<<<<<<< main
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_text_completion
=======
from semantic_kernel.utils.telemetry.model_diagnostics import trace_text_completion
>>>>>>> ms/features/bugbash-prep
=======
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import StreamingTextContent, TextContent
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import (
        PromptExecutionSettings,
    )

logger: logging.Logger = logging.getLogger(__name__)


class OpenAITextCompletionBase(OpenAIHandler, TextCompletionClientBase):
    """Base class for OpenAI text completion services."""
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OpenAITextPromptExecutionSettings

=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"

=======

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"

>>>>>>> origin/main
=======

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"

>>>>>>> Stashed changes
    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OpenAITextPromptExecutionSettings

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    @override
    @trace_text_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_text_contents(
        self,
        prompt: str,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
        settings: "PromptExecutionSettings",
    ) -> list["TextContent"]:
        if not isinstance(
            settings,
            (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings),
        ):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(
            settings,
            (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings),
        )  # nosec
        assert isinstance(settings, (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings))  # nosec

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
        settings: "OpenAIPromptExecutionSettings",
    ) -> List["TextContent"]:
        """Executes a completion request and returns the result.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {OpenAITextPromptExecutionSettings} -- The settings to use for the completion request.

        Returns:
            List["TextContent"] -- The completion result(s).
        """
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        if isinstance(settings, OpenAITextPromptExecutionSettings):
            settings.prompt = prompt
        else:
            settings.messages = [{"role": "user", "content": prompt}]

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes

        response = await self._send_request(request_settings=settings)
        assert isinstance(response, (TextCompletion, ChatCompletion))  # nosec

        metadata = self._get_metadata_from_text_response(response)
        return [
            self._create_text_content(response, choice, metadata)
            for choice in response.choices
        ]

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
>>>>>>> Stashed changes

        response = await self._send_request(request_settings=settings)
        assert isinstance(response, (TextCompletion, ChatCompletion))  # nosec

        metadata = self._get_metadata_from_text_response(response)
        return [
            self._create_text_content(response, choice, metadata)
            for choice in response.choices
        ]

<<<<<<< Updated upstream
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======

        response = await self._send_request(request_settings=settings)
        assert isinstance(response, (TextCompletion, ChatCompletion))  # nosec

        metadata = self._get_metadata_from_text_response(response)
        return [
            self._create_text_content(response, choice, metadata)
            for choice in response.choices
        ]

>>>>>>> origin/main
    @override
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        if not isinstance(
            settings,
            (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings),
        ):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(
            settings,
            (OpenAITextPromptExecutionSettings, OpenAIChatPromptExecutionSettings),
        )  # nosec

        if isinstance(settings, OpenAITextPromptExecutionSettings):
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
            settings.prompt = prompt
        else:
            if not settings.messages:
                settings.messages = [{"role": "user", "content": prompt}]
            else:
                settings.messages.append({"role": "user", "content": prompt})
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.stream = True

<<<<<<< Updated upstream
=======

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.stream = True

>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        response = await self._send_request(request_settings=settings)
        assert isinstance(response, AsyncStream)  # nosec

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            assert isinstance(chunk, (TextCompletion, ChatCompletionChunk))  # nosec
            chunk_metadata = self._get_metadata_from_text_response(chunk)
            yield [
                self._create_streaming_text_content(chunk, choice, chunk_metadata)
                for choice in chunk.choices
            ]

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
        text = (
            choice.text
            if isinstance(choice, TextCompletionChoice)
            else choice.message.content
        )
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
        text = (
            choice.text
            if isinstance(choice, TextCompletionChoice)
            else choice.delta.content
        )
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
        if hasattr(response, "usage"):
            ret["usage"] = response.usage
        return ret

    def _get_metadata_from_text_choice(
        self,
        choice: TextCompletionChoice | ChatCompletionChoice | ChatCompletionChunkChoice,
    ) -> dict[str, Any]:
        """Get metadata from a completion choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }
