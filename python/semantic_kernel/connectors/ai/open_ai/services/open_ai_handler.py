# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import List, Union

from numpy import array
from openai import AsyncOpenAI, AsyncStream
from openai.types import Completion
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from pydantic import Field

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
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
<<<<<<< HEAD
        request_settings: OpenAIRequestSettings,
    ) -> Union[
        ChatCompletion,
        Completion,
        AsyncStream[ChatCompletionChunk],
        AsyncStream[Completion],
    ]:
=======
        request_settings: Union[CompleteRequestSettings, ChatRequestSettings],
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[ChatCompletion, Completion, AsyncStream[ChatCompletionChunk], AsyncStream[Completion],]:
>>>>>>> 9c8afa87 (set line-length for black in sync with Ruff, run black.)
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
            response = await (
                self.client.chat.completions.create(
                    **request_settings.prepare_settings_dict()
                )
                if self.ai_model_type == OpenAIModelTypes.CHAT
                else self.client.completions.create(
                    **request_settings.prepare_settings_dict()
                )
            )
            self.store_usage(response)
            return response
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex
<<<<<<< HEAD

    async def _send_embedding_request(
        self, settings: OpenAIEmbeddingRequestSettings
    ) -> List[array]:
=======
        if not isinstance(response, AsyncStream):
            logger.info(f"OpenAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.completion_tokens += response.usage.completion_tokens
            self.total_tokens += response.usage.total_tokens
        return response

    def _validate_request(self, request_settings, prompt, messages, chat_mode):
        """Validate the request, check if the settings are present and valid."""
        try:
            assert (
                self.ai_model_type != OpenAIModelTypes.EMBEDDING
            ), "The model type is not supported for this operation, please use a text or chat model"
        except AssertionError as exc:
            raise AIException(AIException.ErrorCodes.FunctionTypeNotSupported, exc.args[0], exc) from exc
        try:
            assert request_settings, "The request settings cannot be `None`"
            assert (
                request_settings.max_tokens >= 1
            ), f"The max tokens must be greater than 0, but was {request_settings.max_tokens}"
            if chat_mode:
                assert (
                    prompt or messages
                ), "The messages cannot be `None` or empty, please use either prompt or messages"
            if not chat_mode:
                assert prompt, "The prompt cannot be `None` or empty"
        except AssertionError as exc:
            raise AIException(AIException.ErrorCodes.InvalidRequest, exc.args[0], exc) from exc

    def _create_model_args(
        self,
        request_settings,
        stream,
        prompt,
        messages,
        functions,
        chat_mode,
    ):
        model_args = self.get_model_args()
        model_args.update(
            {
                "stream": stream,
                "temperature": request_settings.temperature,
                "top_p": request_settings.top_p,
                "stop": (
                    request_settings.stop_sequences
                    if request_settings.stop_sequences is not None and len(request_settings.stop_sequences) > 0
                    else None
                ),
                "max_tokens": request_settings.max_tokens,
                "presence_penalty": request_settings.presence_penalty,
                "frequency_penalty": request_settings.frequency_penalty,
                "logit_bias": (
                    request_settings.token_selection_biases
                    if request_settings.token_selection_biases is not None
                    and len(request_settings.token_selection_biases) > 0
                    else {}
                ),
                "n": request_settings.number_of_responses,
            }
        )
        if not chat_mode:
            model_args["prompt"] = prompt
            if hasattr(request_settings, "logprobs"):
                model_args["logprobs"] = request_settings.logprobs
            return model_args

        model_args["messages"] = messages or [{"role": "user", "content": prompt}]
        if functions and request_settings.function_call is not None:
            model_args["function_call"] = request_settings.function_call
            if request_settings.function_call != "auto":
                model_args["functions"] = [func for func in functions if func["name"] == request_settings.function_call]
            else:
                model_args["functions"] = functions

        return model_args

    async def _send_embedding_request(self, texts: List[str], batch_size: Optional[int] = None) -> ndarray:
        if self.ai_model_type != OpenAIModelTypes.EMBEDDING:
            raise AIException(
                AIException.ErrorCodes.FunctionTypeNotSupported,
                "The model type is not supported for this operation, please use an embedding model",
            )
        model_args = self.get_model_args()
>>>>>>> 9c8afa87 (set line-length for black in sync with Ruff, run black.)
        try:
            response = await self.client.embeddings.create(
                **settings.prepare_settings_dict()
            )
            self.store_usage(response)
            # make numpy arrays from the response
            # TODO: the openai response is cast to a list[float], could be used instead of nparray
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
