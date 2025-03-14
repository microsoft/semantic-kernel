# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import Any, ClassVar, Union

from openai import AsyncOpenAI, AsyncStream
from openai.types import CreateEmbeddingResponse

from semantic_kernel.connectors.ai.nvidia import (
    NvidiaPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.nvidia.services.nvidia_model_types import NvidiaModelTypes
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)

RESPONSE_TYPE = Union[list[Any],]


class NvidiaHandler(KernelBaseModel, ABC):
    """Internal class for calls to Nvidia API's."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "nvidia"
    client: AsyncOpenAI
    ai_model_type: NvidiaModelTypes = (
        NvidiaModelTypes.EMBEDDING
    )  # TODO: revert this to chat after adding support for chat-compl  # noqa: TD002
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def _send_request(self, settings: PromptExecutionSettings) -> RESPONSE_TYPE:
        """Send a request to the Nvidia API."""
        if self.ai_model_type == NvidiaModelTypes.EMBEDDING:
            assert isinstance(settings, NvidiaPromptExecutionSettings)  # nosec
            return await self._send_embedding_request(settings)

        raise NotImplementedError(f"Model type {self.ai_model_type} is not supported")

    async def _send_embedding_request(self, settings: NvidiaPromptExecutionSettings) -> list[Any]:
        """Send a request to the OpenAI embeddings endpoint."""
        try:
            # unsupported parameters are internally excluded from main dict and added to extra_body
            response = await self.client.embeddings.create(**settings.prepare_settings_dict())

            self.store_usage(response)
            return [x.embedding for x in response.data]
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to generate embeddings",
                ex,
            ) from ex

    def store_usage(
        self,
        response: CreateEmbeddingResponse,
    ):
        """Store the usage information from the response."""
        if not isinstance(response, AsyncStream) and response.usage:
            logger.info(f"OpenAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.total_tokens += response.usage.total_tokens
            if hasattr(response.usage, "completion_tokens"):
                self.completion_tokens += response.usage.completion_tokens

    def to_dict(self) -> dict[str, str]:
        """Create a dict of the service settings."""
        client_settings = {
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
