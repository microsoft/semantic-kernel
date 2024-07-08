# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any

from ollama import AsyncClient

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent

logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(TextCompletionClientBase, ChatCompletionClientBase):
    """Initializes a new instance of the OllamaChatCompletion class.

    Make sure to have the ollama service running either locally or remotely.
    """

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: OllamaChatPromptExecutionSettings,
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
        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await AsyncClient().chat(model=self.ai_model_id, messages=prepared_chat_history, stream=False)
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
        settings: OllamaChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Streams a text completion using an Ollama model.

        Note that this method does not support multiple responses.

        Args:
            chat_history (ChatHistory): A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings (OllamaChatPromptExecutionSettings): Request settings.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            List[StreamingChatMessageContent]: Stream of StreamingChatMessageContent objects.
        """
        prepared_chat_history = self._prepare_chat_history_for_request(chat_history)

        response_object = await AsyncClient().chat(model=self.ai_model_id, messages=prepared_chat_history, stream=True)
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
        settings: OllamaChatPromptExecutionSettings,
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): A prompt to complete
            settings (OllamaChatPromptExecutionSettings): Settings for the request.

        Returns:
            List["TextContent"]: The completion result(s).
        """
        prepared_chat_history = [{"role": AuthorRole.USER, "content": prompt}]

        response_object = await AsyncClient().chat(model=self.ai_model_id, messages=prepared_chat_history, stream=False)
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
        settings: OllamaChatPromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        """Streams a text completion using an Ollama model.

        Note that this method does not support multiple responses.

        Args:
            prompt (str): A chat history that contains the prompt to complete.
            settings (OllamaChatPromptExecutionSettings): Request settings.

        Yields:
            List["StreamingTextContent"]: The result stream made up of StreamingTextContent objects.
        """
        prepared_chat_history = [{"role": AuthorRole.USER, "content": prompt}]

        response_object = await AsyncClient().chat(model=self.ai_model_id, messages=prepared_chat_history, stream=True)
        async for part in response_object:
            yield [
                StreamingTextContent(
                    choice_index=0,
                    inner_content=part,
                    ai_model_id=self.ai_model_id,
                    text=part.get("message", {"content": None}).get("content", None),
                )
            ]

    def get_prompt_execution_settings_class(self) -> "OllamaChatPromptExecutionSettings":
        """Get the request settings class."""
        return OllamaChatPromptExecutionSettings
