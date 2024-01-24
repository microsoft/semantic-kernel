# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import AsyncIterable, Dict, List, Optional

import aiohttp
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.ollama.ollama_request_settings import (
    OllamaChatRequestSettings,
)
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.models.contents.chat_message_content import ChatMessageContent
from semantic_kernel.models.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.models.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.models.contents.text_content import TextContent

logger: logging.Logger = logging.getLogger(__name__)


class OllamaChatCompletion(TextCompletionClientBase, ChatCompletionClientBase, AIServiceClientBase):
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
        messages: List[Dict[str, str]],
        request_settings: OllamaChatRequestSettings,
        **kwargs,
    ) -> List[ChatMessageContent]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a
                set of messages, from system, user, assistant and function.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging. (Deprecated)

        Returns:
            List[ChatMessageContent] -- A list of ChatMessageContent objects representing the response(s) from the LLM.
        """
        request_settings.messages = messages
        request_settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=request_settings.prepare_settings_dict()) as response:
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
        messages: List[Dict[str, str]],
        settings: OllamaChatRequestSettings,
        **kwargs,
    ) -> AsyncIterable[List[StreamingChatMessageContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {OllamaChatRequestSettings} -- Request settings.

        Yields:
            List[StreamingChatMessageContent] -- Stream of StreamingChatMessageContent objects.
        """
        settings.messages = messages
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
        request_settings: OllamaChatRequestSettings,
        **kwargs,
    ) -> List[TextContent]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

        Returns:
            List["TextContent"] -- The completion result(s).
        """
        request_settings.messages = [{"role": "user", "content": prompt}]
        request_settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=request_settings.prepare_settings_dict()) as response:
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
        settings: OllamaChatRequestSettings,
        **kwargs,
    ) -> AsyncIterable[List[StreamingTextContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {OllamaChatRequestSettings} -- Request settings.

        Yields:
            List["StreamingTextContent"] -- The result stream made up of StreamingTextContent objects.
        """

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

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Get the request settings class."""
        return OllamaChatRequestSettings
