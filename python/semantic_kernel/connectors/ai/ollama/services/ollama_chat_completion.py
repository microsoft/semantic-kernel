# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from ollama import AsyncClient, Message
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(OllamaBase, TextCompletionClientBase, ChatCompletionClientBase):
    """Initializes a new instance of the OllamaChatCompletion class.

    Make sure to have the ollama service running either locally or remotely.
    """

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
                model=ai_model_id,
                host=host,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Ollama settings.", ex) from ex

        super().__init__(
            service_id=service_id or ollama_settings.model,
            ai_model_id=ollama_settings.model,
            client=client or AsyncClient(host=ollama_settings.host),
        )

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        """This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Args:
            chat_history (ChatHistory): A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            List[ChatMessageContent]: A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
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

    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Streams a text completion using an Ollama model.

        Note that this method does not support multiple responses.

        Args:
            chat_history (ChatHistory): A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings (PromptExecutionSettings): Request settings.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            List[StreamingChatMessageContent]: Stream of StreamingChatMessageContent objects.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
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

    async def get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): A prompt to complete
            settings (PromptExecutionSettings): Settings for the request.

        Returns:
            List["TextContent"]: The completion result(s).
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        prepared_chat_history = [Message(role=AuthorRole.USER.value, content=prompt)]

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
            TextContent(
                inner_content=response_object,
                ai_model_id=self.ai_model_id,
                text=response_object.get("message", {"content": None}).get("content", None),
            )
        ]

    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        """Streams a text completion using an Ollama model.

        Note that this method does not support multiple responses.

        Args:
            prompt (str): A chat history that contains the prompt to complete.
            settings (PromptExecutionSettings): Request settings.

        Yields:
            List["StreamingTextContent"]: The result stream made up of StreamingTextContent objects.
        """
        settings = self.get_prompt_execution_settings_from_settings(settings)
        prepared_chat_history = [Message(role=AuthorRole.USER.value, content=prompt)]

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
                StreamingTextContent(
                    choice_index=0,
                    inner_content=part,
                    ai_model_id=self.ai_model_id,
                    text=part.get("message", {"content": None}).get("content", None),
                )
            ]

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return OllamaChatPromptExecutionSettings
