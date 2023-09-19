# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import openai
from numpy import array, ndarray

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)


class OpenAIModelTypes(Enum):
    TEXT = "text"
    CHAT = "chat"
    EMBEDDING = "embedding"


class OpenAIServiceCalls(AIServiceClientBase, ABC):
    """Internal class for calls to OpenAI API's."""

    model_type: OpenAIModelTypes = OpenAIModelTypes.TEXT

    async def _send_request(
        self,
        request_settings: Union[CompleteRequestSettings, ChatRequestSettings],
        prompt: Optional[str] = None,
        messages: Optional[List[Tuple[str, str]]] = None,
        stream: bool = False,
    ):
        """
        Completes the given prompt. Returns a single string completion.
        Cannot return multiple completions. Cannot return logprobs.

        Arguments:
            prompt {str} -- The prompt to complete.
            messages {List[Tuple[str, str]]} -- A list of tuples, where each tuple is a role and content set.
            request_settings {CompleteRequestSettings} -- The request settings.
            stream {bool} -- Whether to stream the response.

        Returns:
            str -- The completed text.
        """
        if self.model_type == OpenAIModelTypes.EMBEDDING:
            raise ValueError(
                "The model type is not supported for this operation, please use a text or chat model"
            )
        if not prompt and not messages:
            if self.model_type == OpenAIModelTypes.TEXT:
                raise ValueError("The prompt cannot be `None` or empty")
            if self.model_type == OpenAIModelTypes.CHAT:
                raise ValueError(
                    "The messages cannot be `None` or empty, please use either prompt or messages"
                )
        if request_settings is None:
            raise ValueError("The request settings cannot be `None`")

        if request_settings.max_tokens < 1:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The max tokens must be greater than 0, "
                f"but was {request_settings.max_tokens}",
            )

        base_args = {
            "api_key": self.api_key,
            "stream": stream,
            "temperature": request_settings.temperature,
            "top_p": request_settings.top_p,
            "stop": (
                request_settings.stop_sequences
                if request_settings.stop_sequences is not None
                and len(request_settings.stop_sequences) > 0
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
        if hasattr(request_settings, "logprobs"):
            base_args["logprobs"] = request_settings.logprobs

        model_args = self.get_model_args()
        model_args.update(base_args)

        if self.model_type == OpenAIModelTypes.CHAT:
            if messages:
                model_args["messages"] = [
                    {"role": role, "content": message} for role, message in messages
                ]
            if prompt:
                model_args["messages"] = [{"role": "user", "content": prompt}]
            if "messages" not in model_args:
                raise ValueError(
                    "The messages cannot be `None` or empty, please use either prompt or messages"
                )
        if self.model_type == OpenAIModelTypes.TEXT:
            model_args["prompt"] = prompt
            if "prompt" not in model_args:
                raise ValueError(
                    "The prompt cannot be `None` or empty, please use the prompt"
                )

        try:
            if self.model_type == OpenAIModelTypes.CHAT:
                response: Any = await openai.ChatCompletion.acreate(**model_args)
            if self.model_type == OpenAIModelTypes.TEXT:
                response: Any = await openai.Completion.acreate(**model_args)
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to complete the prompt",
                ex,
            ) from ex

        return response

    async def _send_embedding_request(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        if self.model_type != OpenAIModelTypes.EMBEDDING:
            raise ValueError(
                "The model type is not supported for this operation, please use an embedding model"
            )
        model_args = self.get_model_args()
        model_args["api_key"] = self.api_key
        try:
            raw_embeddings = []
            batch_size = batch_size or len(texts)
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                response: Any = await openai.Embedding.acreate(
                    **model_args,
                    input=batch,
                )
                # make numpy arrays from the response
                raw_embeddings.extend([array(x["embedding"]) for x in response["data"]])
            return array(raw_embeddings)
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to generate embeddings",
                ex,
            ) from ex

    @abstractmethod
    def get_model_args(self) -> Dict[str, Any]:
        """Return the model args for the specific openai api."""


def _parse_choices(chunk):
    message = ""
    if "role" in chunk.choices[0].delta:
        message += chunk.choices[0].delta.role + ": "
    if "content" in chunk.choices[0].delta:
        message += chunk.choices[0].delta.content

    index = chunk.choices[0].index
    return message, index
