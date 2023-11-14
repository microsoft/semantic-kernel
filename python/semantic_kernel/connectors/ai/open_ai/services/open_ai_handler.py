# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from numpy import array, ndarray
from openai import AsyncOpenAI
from pydantic import Field

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)


class OpenAIHandler(AIServiceClientBase, ABC):
    """Internal class for calls to OpenAI API's."""

    client: AsyncOpenAI
    model_type: OpenAIModelTypes = OpenAIModelTypes.TEXT
    prompt_tokens: int = Field(0, init=False)
    completion_tokens: int = Field(0, init=False)
    total_tokens: int = Field(0, init=False)

    async def _send_request(
        self,
        request_settings: Union[CompleteRequestSettings, ChatRequestSettings],
        prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        functions: Optional[List[Dict[str, Any]]] = None,
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
        if hasattr(request_settings, "logprobs") and self.model_type == OpenAIModelTypes.TEXT:
            base_args["logprobs"] = request_settings.logprobs

        model_args = self.get_model_args()
        model_args.update(base_args)

        if self.model_type == OpenAIModelTypes.CHAT:
            model_args["messages"] = messages or [{"role": "user", "content": prompt}]
            if functions and request_settings.function_call is not None:
                model_args["function_call"] = request_settings.function_call
                if request_settings.function_call != "auto":
                    model_args["functions"] = [
                        func
                        for func in functions
                        if func["name"] == request_settings.function_call
                    ]
                else:
                    model_args["functions"] = functions
        if self.model_type == OpenAIModelTypes.TEXT:
            model_args["prompt"] = prompt
            if "prompt" not in model_args:
                raise ValueError(
                    "The prompt cannot be `None` or empty, please use the prompt"
                )

        try:
            response: Any = await (
                self.client.chat.completions.create(**model_args)
                if self.model_type == OpenAIModelTypes.CHAT
                else self.client.completions.create(**model_args)
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to complete the prompt",
                ex,
            ) from ex

        if not stream and response.usage is not None:
            self.log.info(f"OpenAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.completion_tokens += response.usage.completion_tokens
            self.total_tokens += response.usage.total_tokens

        return response

    async def _send_embedding_request(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        if self.model_type != OpenAIModelTypes.EMBEDDING:
            raise ValueError(
                "The model type is not supported for this operation, please use an embedding model"
            )
        model_args = self.get_model_args()
        try:
            raw_embeddings = []
            batch_size = batch_size or len(texts)
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]  # noqa: E203
                response: Any = await self.client.embeddings.create(
                    input=batch,
                    **model_args,
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
