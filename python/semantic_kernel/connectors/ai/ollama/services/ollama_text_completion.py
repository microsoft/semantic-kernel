# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any

from ollama import AsyncClient
from pydantic import ValidationError

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)


class OllamaTextCompletion(OllamaBase, TextCompletionClientBase):
    """Initializes a new instance of the OllamaTextCompletion class.

    Make sure to have the ollama service running either locally or remotely.
    """

    def __init__(
        self,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        host: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OllamaChatCompletion service.

        Args:
            service_id (Optional[str]): Service ID tied to the execution settings. (Optional)
            ai_model_id (Optional[str]): The model name. (Optional)
            host (Optional[str]): URL of the Ollama server, defaults to None and
                will use the default Ollama service address: http://127.0.0.1:11434. (Optional)
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
            host=ollama_settings.host,
        )

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
            model=self.ai_model_id,
            prompt=prompt,
            stream=False,
            **settings.prepare_settings_dict(),
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
            model=self.ai_model_id,
            prompt=prompt,
            stream=True,
            **settings.prepare_settings_dict(),
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
