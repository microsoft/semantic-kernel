# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp
from pydantic import HttpUrl

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.utils import AsyncSession
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent

logger: logging.Logger = logging.getLogger(__name__)


class OllamaTextCompletion(TextCompletionClientBase):
    """Initializes a new instance of the OllamaTextCompletion class.

    Make sure to have the ollama service running either locally or remotely.

    Args:
        ai_model_id (str): Ollama model name, see https://ollama.ai/library
        url (Optional[Union[str, HttpUrl]]): URL of the Ollama server, defaults to http://localhost:11434/api/generate
    """

    url: HttpUrl = "http://localhost:11434/api/generate"
    session: aiohttp.ClientSession | None = None

    async def get_text_contents(
        self,
        prompt: str,
        settings: OllamaTextPromptExecutionSettings,
    ) -> list[TextContent]:
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (OllamaTextPromptExecutionSettings): Settings for the request.

        Returns:
            List[TextContent]: A list of TextContent objects representing the response(s) from the LLM.
        """
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.prompt = prompt
        settings.stream = False
        async with (
            AsyncSession(self.session) as session,
            session.post(self.url, json=settings.prepare_settings_dict()) as response,
        ):
            response.raise_for_status()
            inner_content = await response.json()
            text = inner_content["response"]
            return [TextContent(inner_content=inner_content, ai_model_id=self.ai_model_id, text=text)]

    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: OllamaTextPromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        """Streams a text completion using an Ollama model.

        Note that this method does not support multiple responses,
        but the result will be a list anyway.

        Args:
            prompt (str): Prompt to complete.
            settings (OllamaTextPromptExecutionSettings): Request settings.

        Yields:
            List[StreamingTextContent]: Completion result.
        """
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        settings.prompt = prompt
        settings.stream = True
        async with (
            AsyncSession(self.session) as session,
            session.post(self.url, json=settings.prepare_settings_dict()) as response,
        ):
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

    def get_prompt_execution_settings_class(self) -> "OllamaTextPromptExecutionSettings":
        """Get the request settings class."""
        return OllamaTextPromptExecutionSettings
