# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import AsyncIterable, List, Optional

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
from semantic_kernel.models.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.models.contents.text_content import TextContent

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
        settings: OllamaTextRequestSettings,
        **kwargs,
    ) -> List[TextContent]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {OllamaTextRequestSettings} -- Settings for the request.

        Returns:
            List[TextContent] -- A list of TextContent objects representing the response(s) from the LLM.
        """
        settings.prompt = prompt
        settings.stream = False
        async with AsyncSession(self.session) as session:
            async with session.post(self.url, json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                text = await response.text()
                return [TextContent(inner_content=text, ai_model_id=self.ai_model_id, text=text)]

    async def complete_stream(
        self,
        prompt: str,
        settings: OllamaTextRequestSettings,
        **kwargs,
    ) -> AsyncIterable[List[StreamingTextContent]]:
        """
        Streams a text completion using a Ollama model.
        Note that this method does not support multiple responses,
        but the result will be a list anyway.

        Arguments:
            prompt {str} -- Prompt to complete.
            request_settings {OllamaTextRequestSettings} -- Request settings.

        Yields:
            List[StreamingTextContent] -- Completion result.
        """
        settings.prompt = prompt
        settings.stream = True
        async with AsyncSession(self.session) as session:
            async with session.post(self.url, json=settings.prepare_settings_dict()) as response:
                response.raise_for_status()
                async for line in response.content:
                    body = json.loads(line)
                    if body.get("done") and body.get("response") is None:
                        break
                    yield [
                        StreamingTextContent(
                            choice_index=0, inner_content=body, ai_model_id=self.ai_model_id, text=body.get("response")
                        )
                    ]
                    if body.get("done"):
                        break

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Get the request settings class."""
        return OllamaTextRequestSettings
