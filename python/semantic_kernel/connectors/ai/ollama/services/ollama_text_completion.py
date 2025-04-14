# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import httpx
from ollama import AsyncClient
from ollama._types import GenerateResponse
from pydantic import ValidationError

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_streaming_text_completion,
    trace_text_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

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
            ollama_settings = OllamaSettings(
                text_model_id=ai_model_id,
                host=host,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Ollama settings.", ex) from ex

        if not ollama_settings.text_model_id:
            raise ServiceInitializationError("Ollama text model ID is required.")

        super().__init__(
            service_id=service_id or ollama_settings.text_model_id,
            ai_model_id=ollama_settings.text_model_id,
            client=client or AsyncClient(host=ollama_settings.host),
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OllamaTextPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        if hasattr(self.client, "_client") and isinstance(self.client._client, httpx.AsyncClient):
            # Best effort to get the endpoint
            return str(self.client._client.base_url)
        return None

    @override
    @trace_text_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        if not isinstance(settings, OllamaTextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OllamaTextPromptExecutionSettings)  # nosec

        response_object = await self.client.generate(
            model=self.ai_model_id,
            prompt=prompt,
            stream=False,
            **settings.prepare_settings_dict(),
        )

        if not isinstance(response_object, (Mapping, GenerateResponse)):
            raise ServiceInvalidResponseError(
                "Invalid response type from Ollama chat completion. "
                f"Expected Mapping or GenerateResponse but got {type(response_object)}."
            )
        return [
            TextContent(
                inner_content=response_object,
                ai_model_id=self.ai_model_id,
                text=response_object.response
                if isinstance(response_object, GenerateResponse)
                else response_object["response"],
            )
        ]

    @override
    @trace_streaming_text_completion(OllamaBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        if not isinstance(settings, OllamaTextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OllamaTextPromptExecutionSettings)  # nosec

        response_object = await self.client.generate(
            model=self.ai_model_id,
            prompt=prompt,
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
                    text=part.response if isinstance(part, GenerateResponse) else part.get("response"),
                )
            ]

    # endregion
