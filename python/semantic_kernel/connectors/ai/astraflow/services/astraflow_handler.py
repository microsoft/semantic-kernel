# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import Any, ClassVar, Union

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.completion import Completion
from openai.types.create_embedding_response import CreateEmbeddingResponse

from semantic_kernel.connectors.ai.astraflow.prompt_execution_settings.astraflow_prompt_execution_settings import (
    AstraflowChatPromptExecutionSettings,
    AstraflowEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.astraflow.services.astraflow_model_types import AstraflowModelTypes
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)

RESPONSE_TYPE = Union[list[Any], ChatCompletion, Completion, AsyncStream[Any]]


class AstraflowHandler(KernelBaseModel, ABC):
    """Internal class for calls to the Astraflow API."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "astraflow"
    client: AsyncOpenAI
    ai_model_type: AstraflowModelTypes = AstraflowModelTypes.CHAT
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0

    async def _send_request(self, settings: PromptExecutionSettings) -> RESPONSE_TYPE:
        """Send a request to the Astraflow API."""
        if self.ai_model_type == AstraflowModelTypes.EMBEDDING:
            assert isinstance(settings, AstraflowEmbeddingPromptExecutionSettings)  # nosec
            return await self._send_embedding_request(settings)
        if self.ai_model_type == AstraflowModelTypes.CHAT:
            assert isinstance(settings, AstraflowChatPromptExecutionSettings)  # nosec
            return await self._send_chat_completion_request(settings)

        raise NotImplementedError(f"Model type {self.ai_model_type} is not supported")

    async def _send_embedding_request(self, settings: AstraflowEmbeddingPromptExecutionSettings) -> list[Any]:
        """Send a request to the Astraflow embeddings endpoint."""
        try:
            response = await self.client.embeddings.create(**settings.prepare_settings_dict())
            self.store_usage(response)
            return [x.embedding for x in response.data]
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to generate embeddings",
                ex,
            ) from ex

    async def _send_chat_completion_request(
        self, settings: AstraflowChatPromptExecutionSettings
    ) -> ChatCompletion | AsyncStream[Any]:
        """Send a request to the Astraflow chat completion endpoint."""
        try:
            response = await self.client.chat.completions.create(**settings.prepare_settings_dict())
            self.store_usage(response)
            return response
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the chat",
                ex,
            ) from ex

    def store_usage(
        self,
        response: ChatCompletion
        | Completion
        | AsyncStream[ChatCompletionChunk]
        | AsyncStream[Completion]
        | CreateEmbeddingResponse,
    ) -> None:
        """Store the usage information from the response."""
        if not isinstance(response, AsyncStream) and response.usage:
            logger.info(f"Astraflow usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.total_tokens += response.usage.total_tokens
            if hasattr(response.usage, "completion_tokens"):
                self.completion_tokens += response.usage.completion_tokens

    def to_dict(self) -> dict[str, str]:
        """Create a dict of the service settings."""
        client_settings: dict[str, Any] = {
            "api_key": self.client.api_key,
            "default_headers": {k: v for k, v in self.client.default_headers.items() if k != USER_AGENT},
        }
        if self.client.organization:
            client_settings["org_id"] = self.client.organization
        base = self.model_dump(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "ai_model_type",
                "service_id",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base
