# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Any, AsyncIterable, List, Optional

import aiohttp
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent

logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(TextCompletionClientBase, ChatCompletionClientBase):
    """
    Initializes a new instance of the OllamaChatCompletion class.

    Make sure to have the ollama service running either locally or remotely.

    Arguments:
        ai_model_id {str} -- Ollama model name, see https://ollama.ai/library
        url {Optional[Union[str, HttpUrl]]} -- URL of the Ollama server, defaults to http://localhost:11434/api/chat
        session {Optional[aiohttp.ClientSession]} -- Optional client session to use for requests.
    """

    url: HttpUrl = "http://localhost:11434/api/chat"
    session: Optional[aiohttp.ClientSession] = None

    async def complete_chat(
        self,
        chat_history: ChatHistory,
        settings: OllamaChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> List[ChatMessageContent]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            chat_history {ChatHistory} -- A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings {PromptExecutionSettings} -- Settings for the request.
            kwargs {Dict[str, Any]} -- The optional arguments.

        Returns:
            List[ChatMessageContent] -- A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                response_object = await response.json()
                return [
                    ChatMessageContent(
                        inner_content=response_object,
                        ai_model_id=self.ai_model_id,
                        role="assistant",
                        content=response_object.get("message", {"content": None}).get("content", None),
                    )
                ]

    async def complete_chat_stream(
        self,
        chat_history: ChatHistory,
        settings: OllamaChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncIterable[List[StreamingChatMessageContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            chat_history {ChatHistory} -- A chat history that contains a list of chat messages,
                that can be rendered into a set of messages, from system, user, assistant and function.
            settings {OllamaChatPromptExecutionSettings} -- Request settings.
            kwargs {Dict[str, Any]} -- The optional arguments.

        Yields:
            List[StreamingChatMessageContent] -- Stream of StreamingChatMessageContent objects.
        """
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = True
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                async for line in response.content:
                    body = json.loads(line)
                    if body.get("done") and body.get("message", {}).get("content") is None:
                        break
                    yield [
                        StreamingChatMessageContent(
                            choice_index=0,
                            inner_content=body,
                            ai_model_id=self.ai_model_id,
                            content=body.get("message", {"content": None}).get("content", None),
                        )
                    ]
                    if body.get("done"):
                        break

    async def complete(
        self,
        prompt: str,
        settings: OllamaChatPromptExecutionSettings,
    ) -> List[TextContent]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            chat_history {ChatHistory} -- A chat history that contains the prompt to complete.
            settings {OllamaChatPromptExecutionSettings} -- Settings for the request.

        Returns:
            List["TextContent"] -- The completion result(s).
        """
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.messages = [{"role": "user", "content": prompt}]
        settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                response_object = await response.json()
                return [
                    TextContent(
                        inner_content=response_object,
                        ai_model_id=self.ai_model_id,
                        text=response_object.get("message", {"content": None}).get("content", None),
                    )
                ]

    async def complete_stream(
        self,
        prompt: str,
        settings: OllamaChatPromptExecutionSettings,
    ) -> AsyncIterable[List[StreamingTextContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- A chat history that contains the prompt to complete.
            settings {OllamaChatPromptExecutionSettings} -- Request settings.

        Yields:
            List["StreamingTextContent"] -- The result stream made up of StreamingTextContent objects.
        """

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.messages = [{"role": "user", "content": prompt}]
        settings.stream = True
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                async for line in response.content:
                    body = json.loads(line)
                    if body.get("done") and body.get("message", {}).get("content") is None:
                        break
                    yield [
                        StreamingTextContent(
                            choice_index=0,
                            inner_content=body,
                            ai_model_id=self.ai_model_id,
                            text=body.get("message", {"content": None}).get("content", None),
                        )
                    ]
                    if body.get("done"):
                        break

    def get_prompt_execution_settings_class(self) -> "OllamaChatPromptExecutionSettings":
        """Get the request settings class."""
        return OllamaChatPromptExecutionSettings
