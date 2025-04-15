# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import httpx
from ollama import AsyncClient
from ollama._types import ChatResponse, Message
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.ollama.services.utils import (
    MESSAGE_CONVERTERS,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import STREAMING_CMC_ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

CMC_TYPE = TypeVar("CMC_TYPE", bound=ChatMessageContent)

logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(OllamaBase, ChatCompletionClientBase):
    """Initializes a new instance of the OllamaChatCompletion class.

    Make sure to have the ollama service running either locally or remotely.
    """

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

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
            ollama_settings = OllamaSettings(
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
    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[Message]:
        return [MESSAGE_CONVERTERS[message.role](message) for message in chat_history.messages]

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if settings.function_choice_behavior and settings.function_choice_behavior.type_ in [
            FunctionChoiceType.REQUIRED,
            FunctionChoiceType.NONE,
        ]:
            raise ServiceInvalidExecutionSettingsError(
                "Ollama does not support function choice behavior of type 'required' or 'none' yet."
            )

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[["FunctionCallChoiceConfiguration", "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_choice_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tools"):
            settings.tools = None

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

        if isinstance(response_object, ChatResponse):
            return [self._create_chat_message_content_from_chat_response(response_object)]
        if isinstance(response_object, Mapping):
            return [self._create_chat_message_content(response_object)]
        raise ServiceInvalidResponseError(
            "Invalid response type from Ollama chat completion. "
            f"Expected Mapping or ChatResponse but got {type(response_object)}."
        )

    @override
    @trace_streaming_chat_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
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
                "Invalid response type from Ollama streaming chat completion. "
                f"Expected AsyncIterator but got {type(response_object)}."
            )

        async for part in response_object:
            if isinstance(part, ChatResponse):
                yield [self._create_streaming_chat_message_content_from_chat_response(part, function_invoke_attempt)]
                continue
            if isinstance(part, Mapping):
                yield [self._create_streaming_chat_message_content(part, function_invoke_attempt)]
                continue
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama streaming chat completion. "
                f"Expected mapping or ChatResponse but got {type(part)}."
            )

    # endregion

    def _create_streaming_chat_message_content_from_chat_response(
        self,
        response: ChatResponse,
        function_invoke_attempt: int,
    ) -> StreamingChatMessageContent:
        """Create a chat message content from the response."""
        items: list[STREAMING_ITEM_TYPES] = []
        if response.message.content:
            items.append(
                StreamingTextContent(
                    choice_index=0,
                    text=response.message.content,
                    inner_content=response.message,
                )
            )
        self._parse_tool_calls(response.message.tool_calls, items)
        return StreamingChatMessageContent(
            choice_index=0,
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=self._get_metadata_from_chat_response(response),
            function_invoke_attempt=function_invoke_attempt,
        )

    def _parse_tool_calls(self, tool_calls: Sequence[Message.ToolCall] | None, items: list[Any]):
        if tool_calls:
            for tool_call in tool_calls:
                items.append(
                    FunctionCallContent(
                        inner_content=tool_call,
                        ai_model_id=self.ai_model_id,
                        name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                    )
                )

    def _create_chat_message_content_from_chat_response(self, response: ChatResponse) -> ChatMessageContent:
        """Create a chat message content from the response."""
        items: list[CMC_ITEM_TYPES] = []
        if response.message.content:
            items.append(
                TextContent(
                    text=response.message.content,
                    inner_content=response.message,
                )
            )
        self._parse_tool_calls(response.message.tool_calls, items)
        return ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=self._get_metadata_from_chat_response(response),
        )

    def _create_chat_message_content(self, response: Mapping[str, Any]) -> ChatMessageContent:
        """Create a chat message content from the response."""
        items: list[CMC_ITEM_TYPES] = []
        if not (message := response.get("message", None)):
            raise ServiceInvalidResponseError("No message content found in response.")

        if content := message.get("content", None):
            items.append(
                TextContent(
                    text=content,
                    inner_content=message,
                )
            )
        if tool_calls := message.get("tool_calls", None):
            for tool_call in tool_calls:
                items.append(
                    FunctionCallContent(
                        inner_content=tool_call,
                        ai_model_id=self.ai_model_id,
                        name=tool_call.get("function").get("name"),
                        arguments=tool_call.get("function").get("arguments"),
                    )
                )

        return ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            metadata=self._get_metadata_from_response(response),
        )

    def _create_streaming_chat_message_content(
        self, part: Mapping[str, Any], function_invoke_attempt: int
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content from the response part."""
        items: list[STREAMING_ITEM_TYPES] = []
        if not (message := part.get("message", None)):
            raise ServiceInvalidResponseError("No message content found in response part.")

        if content := message.get("content", None):
            items.append(
                StreamingTextContent(
                    choice_index=0,
                    text=content,
                    inner_content=message,
                )
            )
        if tool_calls := message.get("tool_calls", None):
            for tool_call in tool_calls:
                items.append(
                    FunctionCallContent(
                        inner_content=tool_call,
                        ai_model_id=self.ai_model_id,
                        name=tool_call.get("function").get("name"),
                        arguments=tool_call.get("function").get("arguments"),
                    )
                )

        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            items=items,
            inner_content=part,
            ai_model_id=self.ai_model_id,
            metadata=self._get_metadata_from_response(part),
            function_invoke_attempt=function_invoke_attempt,
        )

    def _get_metadata_from_response(self, response: Mapping[str, Any]) -> dict[str, Any]:
        """Get metadata from the response."""
        metadata = {
            "model": response.get("model"),
        }

        if "prompt_eval_count" in response and "eval_count" in response:
            metadata["usage"] = CompletionUsage(
                prompt_tokens=response.get("prompt_eval_count"),
                completion_tokens=response.get("eval_count"),
            )

        return metadata

    def _get_metadata_from_chat_response(self, response: ChatResponse) -> dict[str, Any]:
        """Get metadata from the response."""
        metadata: dict[str, Any] = {
            "model": response.model,
        }
        if response.prompt_eval_count and response.eval_count:
            metadata["usage"] = CompletionUsage(
                prompt_tokens=response.prompt_eval_count,
                completion_tokens=response.eval_count,
            )
        return metadata
