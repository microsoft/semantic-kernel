# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any

from ollama import AsyncClient

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent

logger: logging.Logger = logging.getLogger(__name__)


class OllamaTextCompletion(TextCompletionClientBase):
    """Initializes a new instance of the OllamaTextCompletion class.

    Make sure to have the ollama service running either locally or remotely.

    Args:
        host (Optional[str]): URL of the Ollama server, defaults to None and
            will use the default Ollama service address: http://127.0.0.1:11434
    """

    host: str | None = None

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
        response_object = await AsyncClient(host=self.host).generate(
            model=self.ai_model_id, prompt=prompt, options=settings.options, stream=False
        )

        inner_content = response_object
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
        response_object = await AsyncClient(host=self.host).generate(
            model=self.ai_model_id, prompt=prompt, options=settings.options, stream=True
        )

        async for part in response_object:
            yield [
                StreamingTextContent(
                    choice_index=0, inner_content=part, ai_model_id=self.ai_model_id, text=part.get("response")
                )
            ]

    def get_prompt_execution_settings_class(self) -> "OllamaTextPromptExecutionSettings":
        """Get the request settings class."""
        return OllamaTextPromptExecutionSettings
