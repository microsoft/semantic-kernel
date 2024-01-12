# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Dict, List, Optional, Union

import aiohttp
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.ollama.ollama_request_settings import OllamaChatRequestSettings
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

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

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        request_settings: OllamaChatRequestSettings,
        **kwargs,
    ) -> Union[str, List[str]]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a
                set of messages, from system, user, assistant and function.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging. (Deprecated)

        Returns:
            Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """
        request_settings.messages = messages
        request_settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=request_settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                response_object = await response.json()
                return response_object.get("message", {"content": None}).get("content", None)

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: OllamaChatRequestSettings,
        **kwargs,
    ):
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {OllamaChatRequestSettings} -- Request settings.

        Yields:
            str -- Completion result.
        """
        settings.messages = messages
        settings.stream = True
        async with AsyncSession(self.session) as session:
            async with session.post(str(self.url), json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                async for line in response.content:
                    body = json.loads(line)
                    response_part = body.get("message", {"content": None}).get("content", None)
                    yield response_part
                    if body.get("done"):
                        break

    async def complete_async(
        self,
        prompt: str,
        request_settings: OllamaChatRequestSettings,
        **kwargs,
    ) -> Union[str, List[str]]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

            Returns:
                Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """
        return await self.complete_chat_async([{"role": "user", "content": prompt}], request_settings, **kwargs)

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: OllamaChatRequestSettings,
        **kwargs,
    ):
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {OllamaChatRequestSettings} -- Request settings.

        Yields:
            str -- Completion result.
        """
        response = self.complete_chat_stream_async([{"role": "user", "content": prompt}], request_settings, **kwargs)
        async for line in response:
            yield line

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Get the request settings class."""
        return OllamaChatRequestSettings
