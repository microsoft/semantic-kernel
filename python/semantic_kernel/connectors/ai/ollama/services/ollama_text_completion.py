# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import List, Optional, Union

import aiohttp
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.ollama.ollama_request_settings import (
    OllamaTextRequestSettings,
)
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class OllamaTextCompletion(TextCompletionClientBase, AIServiceClientBase):
    """
    Initializes a new instance of the OllamaTextCompletion class.

    Make sure to have the ollama service running either locally or remotely.

    Arguments:
        ai_model_id {str} -- Ollama model name, see https://ollama.ai/library
        url {Optional[Union[str, HttpUrl]]} -- URL of the Ollama server, defaults to http://localhost:11434/api/generate
    """

    url: HttpUrl = "http://localhost:11434/api/generate"
    session: Optional[aiohttp.ClientSession] = None

    async def complete(
        self,
        prompt: str,
        request_settings: OllamaTextRequestSettings,
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
        request_settings.prompt = prompt
        request_settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(self.url, json=request_settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                return await response.text()

    async def complete_stream(
        self,
        prompt: str,
        request_settings: OllamaTextRequestSettings,
        **kwargs,
    ):
        """
        Streams a text completion using a Hugging Face model.
        Note that this method does not support multiple responses.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {HuggingFaceRequestSettings} -- Request settings.

        Yields:
            str -- Completion result.
        """
        request_settings.prompt = prompt
        request_settings.stream = True
        async with AsyncSession(self.session) as session:
            async with session.post(self.url, json=request_settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                async for line in response.content:
                    body = json.loads(line)
                    response_part = body.get("response")
                    yield response_part
                    if body.get("done"):
                        break

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Get the request settings class."""
        return OllamaTextRequestSettings
