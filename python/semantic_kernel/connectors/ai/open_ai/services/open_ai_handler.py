# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import Any

from openai import AsyncOpenAI, AsyncStream, BadRequestError
from openai.lib.streaming.chat._completions import AsyncChatCompletionStreamManager
from openai.types import Completion, CreateEmbeddingResponse
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import BaseModel

from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import ContentFilterAIException
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.utils.structured_output_schema import generate_structured_output_response_format_schema
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIHandler(KernelBaseModel, ABC):
    """Internal class for calls to OpenAI API's."""

    client: AsyncOpenAI
    ai_model_type: OpenAIModelTypes = OpenAIModelTypes.CHAT
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    async def _send_request(
        self,
        request_settings: OpenAIPromptExecutionSettings,
    ) -> (
        ChatCompletion
        | Completion
        | AsyncStream[ChatCompletionChunk]
        | AsyncStream[Completion]
        | AsyncChatCompletionStreamManager
    ):
        """Execute the appropriate call to OpenAI models."""
        try:
            if self.ai_model_type == OpenAIModelTypes.CHAT:
                if (
                    hasattr(request_settings, "structured_json_response")
                    and hasattr(request_settings, "response_format")
                    and request_settings.structured_json_response
                ):
                    settings = request_settings.prepare_settings_dict()
                    if not issubclass(request_settings.response_format, BaseModel):
                        generated_schema = KernelJsonSchemaBuilder.build(
                            parameter_type=request_settings.response_format, structured_output=True
                        )
                        assert generated_schema is not None  # nosec
                        settings["response_format"] = generate_structured_output_response_format_schema(
                            name=request_settings.response_format.__name__, schema=generated_schema
                        )
                    if settings.pop("stream", None):
                        return self.client.beta.chat.completions.stream(**settings)
                    response = await self.client.beta.chat.completions.parse(**settings)
                else:
                    response = await self.client.chat.completions.create(**request_settings.prepare_settings_dict())
            else:
                response = await self.client.completions.create(**request_settings.prepare_settings_dict())
            self.store_usage(response)
            return response
        except BadRequestError as ex:
            if ex.code == "content_filter":
                raise ContentFilterAIException(
                    f"{type(self)} service encountered a content error",
                    ex,
                ) from ex
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

    async def _send_embedding_request(self, settings: OpenAIEmbeddingPromptExecutionSettings) -> list[Any]:
        try:
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
        response: ChatCompletion
        | Completion
        | AsyncStream[ChatCompletionChunk]
        | AsyncStream[Completion]
        | CreateEmbeddingResponse,
    ):
        """Store the usage information from the response."""
        if not isinstance(response, AsyncStream) and response.usage:
            logger.info(f"OpenAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.total_tokens += response.usage.total_tokens
            if hasattr(response.usage, "completion_tokens"):
                self.completion_tokens += response.usage.completion_tokens
