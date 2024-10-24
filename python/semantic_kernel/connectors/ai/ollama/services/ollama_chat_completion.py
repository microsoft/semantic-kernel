# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import httpx
from ollama import AsyncClient
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(OllamaBase, ChatCompletionClientBase):
    """Initializes a new instance of the OllamaChatCompletion class.

    Make sure to have the ollama service running either locally or remotely.
    """

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

    def __init__(
        self,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        host: str | None = None,
        client: AsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OllamaChatCompletion service.

        Args:
            service_id (Optional[str]): Service ID tied to the execution settings. (Optional)
            ai_model_id (Optional[str]): The model name. (Optional)
            host (Optional[str]): URL of the Ollama server, defaults to None and
                will use the default Ollama service address: http://127.0.0.1:11434. (Optional)
            client (Optional[AsyncClient]): A custom Ollama client to use for the service. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
        """
        try:
            ollama_settings = OllamaSettings.create(
                chat_model_id=ai_model_id,
                host=host,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Ollama settings.", ex) from ex

        if not ollama_settings.chat_model_id:
            raise ServiceInitializationError("Ollama chat model ID is required.")

        super().__init__(
            service_id=service_id or ollama_settings.chat_model_id,
            ai_model_id=ollama_settings.chat_model_id,
            client=client or AsyncClient(host=ollama_settings.host),
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return OllamaChatPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        if hasattr(self.client, "_client") and isinstance(self.client._client, httpx.AsyncClient):
            # Best effort to get the endpoint
            return str(self.client._client.base_url)
        return None

    @override
    @trace_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, OllamaChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OllamaChatPromptExecutionSettings)  # nosec

        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await self.client.chat(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=False,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, Mapping):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected Mapping but got {type(response_object)}."
            )

        return [
            ChatMessageContent(
                inner_content=response_object,
                ai_model_id=self.ai_model_id,
                role=AuthorRole.ASSISTANT,
                content=response_object.get("message", {"content": None}).get("content", None),
            )
        ]

    @override
    @trace_streaming_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, OllamaChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OllamaChatPromptExecutionSettings)  # nosec

        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await self.client.chat(
            model=self.ai_model_id,
            messages=prepared_chat_history,
            stream=True,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, AsyncIterator):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected AsyncIterator but got {type(response_object)}."
            )

        async for part in response_object:
            yield [
                StreamingChatMessageContent(
                    role=AuthorRole.ASSISTANT,
                    choice_index=0,
                    inner_content=part,
                    ai_model_id=self.ai_model_id,
                    content=part.get("message", {"content": None}).get("content", None),
                )
            ]

    # endregion
