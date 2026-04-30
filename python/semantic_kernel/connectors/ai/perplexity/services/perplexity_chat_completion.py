# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Mapping
from copy import copy
from typing import Any

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import ValidationError

from semantic_kernel import __version__ as semantic_kernel_version
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.perplexity.prompt_execution_settings.perplexity_prompt_execution_settings import (
    PerplexityChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.perplexity.settings.perplexity_settings import PerplexitySettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.contents import (
    AuthorRole,
    ChatMessageContent,
    FinishReason,
    StreamingChatMessageContent,
    StreamingTextContent,
    TextContent,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)

# Perplexity attribution header — sent on every outgoing request so the API can
# identify integration traffic. Slug is fixed; version follows the package.
PERPLEXITY_ATTRIBUTION_HEADER = "X-Pplx-Integration"
PERPLEXITY_ATTRIBUTION_SLUG = "semantic-kernel"


def _build_attribution_value() -> str:
    return f"{PERPLEXITY_ATTRIBUTION_SLUG}/{semantic_kernel_version}"


@experimental
class PerplexityChatCompletion(ChatCompletionClientBase):
    """Perplexity chat completion service.

    Perplexity exposes an OpenAI-compatible chat completions endpoint at
    https://api.perplexity.ai/chat/completions, so this connector reuses the
    ``openai`` Python SDK with a custom ``base_url`` and an attribution header.
    """

    client: AsyncOpenAI

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        service_id: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize a PerplexityChatCompletion service.

        Args:
            ai_model_id: Perplexity model name. Defaults to ``sonar-pro``. See
                https://docs.perplexity.ai/api-reference/chat-completions-post for available models.
            api_key: Perplexity API key. If not provided the value from the ``PERPLEXITY_API_KEY``
                environment variable (or ``env_file_path``) is used.
            base_url: Override the API base URL. Defaults to ``https://api.perplexity.ai``.
            service_id: Service ID tied to the execution settings.
            default_headers: Additional default headers to send with every request. The Perplexity
                attribution header is always added.
            async_client: An existing ``AsyncOpenAI`` client to use. If provided, ``api_key`` and
                ``base_url`` are ignored, but the caller is responsible for configuring the
                attribution header on the client.
            env_file_path: Optional path to a ``.env`` file to load settings from.
            env_file_encoding: Encoding of the ``.env`` file.
        """
        try:
            perplexity_settings = PerplexitySettings(
                api_key=api_key,
                chat_model_id=ai_model_id,
                base_url=base_url,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Perplexity settings.", ex) from ex

        if not async_client and not perplexity_settings.api_key:
            raise ServiceInitializationError("The Perplexity API key is required.")

        if not async_client:
            merged_headers: dict[str, str] = dict(copy(default_headers)) if default_headers else {}
            # Attribution header — must be present on every outgoing request.
            merged_headers[PERPLEXITY_ATTRIBUTION_HEADER] = _build_attribution_value()
            if APP_INFO:
                merged_headers.update(APP_INFO)
                merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

            async_client = AsyncOpenAI(
                api_key=perplexity_settings.api_key.get_secret_value() if perplexity_settings.api_key else None,
                base_url=perplexity_settings.base_url,
                default_headers=merged_headers,
            )

        super().__init__(
            ai_model_id=perplexity_settings.chat_model_id,
            service_id=service_id or "",
            client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "PerplexityChatCompletion":
        """Initialize a Perplexity service from a dictionary of settings."""
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            base_url=settings.get("base_url"),
            service_id=settings.get("service_id"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
        )

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return PerplexityChatPromptExecutionSettings

    @override
    def service_url(self) -> str | None:
        return str(self.client.base_url)

    @override
    @trace_chat_completion("perplexity")
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, PerplexityChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, PerplexityChatPromptExecutionSettings)  # nosec

        settings.stream = False
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(settings)
        assert isinstance(response, ChatCompletion)  # nosec
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    @override
    @trace_streaming_chat_completion("perplexity")
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, PerplexityChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, PerplexityChatPromptExecutionSettings)  # nosec

        settings.stream = True
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(settings)
        assert isinstance(response, AsyncStream)  # nosec

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_chat_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata, function_invoke_attempt)
                for choice in chunk.choices
            ]

    async def _send_request(
        self, settings: PerplexityChatPromptExecutionSettings
    ) -> ChatCompletion | AsyncStream[ChatCompletionChunk]:
        """Send a chat completion request to the Perplexity API."""
        try:
            return await self.client.chat.completions.create(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the chat",
                ex,
            ) from ex

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = []
        if choice.message.content:
            items.append(TextContent(text=choice.message.content))

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.message.role),
            items=items,
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
        function_invoke_attempt: int,
    ) -> StreamingChatMessageContent:
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = []
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
        return StreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=(AuthorRole(choice.delta.role) if choice.delta and choice.delta.role else AuthorRole.ASSISTANT),
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
            items=items,
            function_invoke_attempt=function_invoke_attempt,
        )

    def _get_metadata_from_chat_response(self, response: ChatCompletion | ChatCompletionChunk) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
        }
        # Perplexity returns a top-level ``citations`` list alongside the OpenAI-shaped payload;
        # surface it on the metadata so callers can render source attribution.
        citations = getattr(response, "citations", None)
        if citations is not None:
            metadata["citations"] = citations
        return metadata

    def _get_metadata_from_chat_choice(self, choice: Choice | ChunkChoice) -> dict[str, Any]:
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        for message in chat_history.messages:
            messages.append({role_key: message.role.value, content_key: message.content})
        return messages

    def to_dict(self) -> dict[str, str]:
        """Create a dict of the service settings."""
        client_settings = {
            "api_key": self.client.api_key,
            "default_headers": {k: v for k, v in self.client.default_headers.items() if k != USER_AGENT},
        }
        base = self.model_dump(
            exclude={
                "service_id",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base
