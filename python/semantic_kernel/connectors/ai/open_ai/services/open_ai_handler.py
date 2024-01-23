# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import List, Union

from numpy import array, ndarray
from openai import AsyncOpenAI, AsyncStream, BadRequestError
from openai.types import Completion
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import Field

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import (
    ContentFilterAIException,
)
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIEmbeddingRequestSettings,
    OpenAIRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIHandler(AIServiceClientBase, ABC):
    """Internal class for calls to OpenAI API's."""

    client: AsyncOpenAI
    ai_model_type: OpenAIModelTypes = OpenAIModelTypes.CHAT
    prompt_tokens: int = Field(0, init_var=False)
    completion_tokens: int = Field(0, init_var=False)
    total_tokens: int = Field(0, init_var=False)

    async def _send_request(
        self,
        request_settings: OpenAIRequestSettings,
    ) -> Union[ChatCompletion, Completion, AsyncStream[ChatCompletionChunk], AsyncStream[Completion]]:
        """
        Completes the given prompt. Returns a single string completion.
        Cannot return multiple completions. Cannot return logprobs.

        Arguments:
            prompt {str} -- The prompt to complete.
            messages {List[Tuple[str, str]]} -- A list of tuples, where each tuple is a role and content set.
            request_settings {OpenAIRequestSettings} -- The request settings.
            stream {bool} -- Whether to stream the response.

        Returns:
            ChatCompletion, Completion, AsyncStream[Completion | ChatCompletionChunk] -- The completion response.
        """
        try:
            if self.ai_model_type == OpenAIModelTypes.CHAT:
                response = await self.client.chat.completions.create(**request_settings.prepare_settings_dict())
            else:
                response = await self.client.completions.create(**request_settings.prepare_settings_dict())
            self.store_usage(response)
            return response
        except BadRequestError as ex:
            if ex.code == "content_filter":
                raise ContentFilterAIException(
                    AIException.ErrorCodes.BadContentError,
                    f"{type(self)} service encountered a content error",
                    ex,
                )
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

    async def _send_embedding_request(self, settings: OpenAIEmbeddingRequestSettings) -> List[ndarray]:
        try:
            response = await self.client.embeddings.create(**settings.prepare_settings_dict())
            self.store_usage(response)
            # make numpy arrays from the response
            # TODO: the openai response is cast to a list[float], could be used instead of ndarray
            return [array(x.embedding) for x in response.data]
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                f"{type(self)} service failed to generate embeddings",
                ex,
            ) from ex

    def store_usage(self, response):
        if not isinstance(response, AsyncStream):
            logger.info(f"OpenAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.total_tokens += response.usage.total_tokens
            if hasattr(response.usage, "completion_tokens"):
                self.completion_tokens += response.usage.completion_tokens

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Return the class with the applicable request settings."""
        return OpenAIRequestSettings
