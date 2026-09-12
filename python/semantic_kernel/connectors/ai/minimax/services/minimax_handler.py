# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import Any, ClassVar, Union

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.completion import Completion

from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_prompt_execution_settings import (
    MiniMaxChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.minimax.services.minimax_model_types import MiniMaxModelTypes
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import USER_AGENT
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)

RESPONSE_TYPE = Union[list[Any], ChatCompletion, Completion, AsyncStream[Any]]


class MiniMaxHandler(KernelBaseModel, ABC):
    """Internal class for calls to MiniMax API's."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "minimax"
    client: AsyncOpenAI
    ai_model_type: MiniMaxModelTypes = MiniMaxModelTypes.CHAT
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0

    async def _send_request(self, settings: PromptExecutionSettings) -> RESPONSE_TYPE:
        """Send a request to the MiniMax API."""
        if self.ai_model_type == MiniMaxModelTypes.CHAT:
            assert isinstance(settings, MiniMaxChatPromptExecutionSettings)  # nosec
            return await self._send_chat_completion_request(settings)

        raise NotImplementedError(f"Model type {self.ai_model_type} is not supported")

    async def _send_chat_completion_request(
        self, settings: MiniMaxChatPromptExecutionSettings
    ) -> ChatCompletion | AsyncStream[Any]:
        """Send a request to the MiniMax chat completion endpoint."""
        try:
            settings_dict = settings.prepare_settings_dict()
            response = await self.client.chat.completions.create(**settings_dict)
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
        | AsyncStream[Completion],
    ):
        """Store the usage information from the response."""
        if not isinstance(response, AsyncStream) and response.usage:
            logger.info(f"MiniMax usage: {response.usage}")
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
