# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from collections.abc import AsyncGenerator

from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import ChatCompletionResponse, ChatCompletionStreamResponse

from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger: logging.Logger = logging.getLogger(__name__)


class MistralAIHandler(KernelBaseModel, ABC):
    """Internal class for calls to MistralAI API's."""

    client: MistralAsyncClient
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def _send_request(
        self,
        request_settings: MistralAIChatPromptExecutionSettings,
        stream: bool
    ) -> ChatCompletionResponse | AsyncGenerator[ChatCompletionStreamResponse, None]:
        """Completes the given prompt. Returns a single string completion.

        Cannot return multiple completions. Cannot return logprobs.

        Args:
            prompt (str): The prompt to complete.
            messages (List[Tuple[str, str]]): A list of tuples, where each tuple is a role and content set.
            request_settings (MistralAIPromptExecutionSettings): The request settings.
            stream (bool): Whether to stream the response.

        Returns:
            ChatCompletion, Completion, AsyncGenerator[Completion | ChatCompletionChunk]: The completion response.
        """
        try:
            if not stream:
                response = await self.client.chat(**request_settings.prepare_settings_dict())
            else:
                response = self.client.chat_stream(**request_settings.prepare_settings_dict())
            self.store_usage(response)
            return response
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

    def store_usage(self, response):
        """Store the usage information from the response."""
        if not isinstance(response, AsyncGenerator):
            logger.info(f"MistralAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.total_tokens += response.usage.total_tokens
            if hasattr(response.usage, "completion_tokens"):
                self.completion_tokens += response.usage.completion_tokens
