# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import Any, Union

from openai import AsyncOpenAI, AsyncStream, BadRequestError, _legacy_response
from openai.lib._parsing._completions import type_to_response_format_param
from openai.types import Completion, CreateEmbeddingResponse
from openai.types.audio import Transcription
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.images_response import ImagesResponse
from openai.types.responses.response import Response
from pydantic import BaseModel

from semantic_kernel.connectors.ai.open_ai import (
    OpenAIAudioToTextExecutionSettings,
    OpenAIChatPromptExecutionSettings,
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAIPromptExecutionSettings,
    OpenAIResponseExecutionSettings,
    OpenAITextToAudioExecutionSettings,
    OpenAITextToImageExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.exceptions.content_filter_ai_exception import ContentFilterAIException
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.response_usage import ResponseUsage
from semantic_kernel.connectors.utils.structured_output_schema import generate_structured_output_response_format_schema
from semantic_kernel.exceptions import ServiceResponseException
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder

logger: logging.Logger = logging.getLogger(__name__)

RESPONSE_TYPE = Union[
    ChatCompletion,
    Completion,
    AsyncStream[ChatCompletionChunk],
    AsyncStream[Completion],
    list[Any],
    ImagesResponse,
    Transcription,
    _legacy_response.HttpxBinaryResponseContent,
    Response,
]


class OpenAIHandler(KernelBaseModel, ABC):
    """Internal class for calls to OpenAI API's."""

    client: AsyncOpenAI
    ai_model_type: OpenAIModelTypes = OpenAIModelTypes.CHAT
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    response_usage: ResponseUsage | None = None

    async def _send_request(self, settings: PromptExecutionSettings) -> RESPONSE_TYPE:
        """Send a request to the OpenAI API."""
        if self.ai_model_type == OpenAIModelTypes.TEXT or self.ai_model_type == OpenAIModelTypes.CHAT:
            assert isinstance(settings, OpenAIPromptExecutionSettings)  # nosec
            return await self._send_completion_request(settings)
        if self.ai_model_type == OpenAIModelTypes.RESPONSE:
            assert isinstance(settings, OpenAIResponseExecutionSettings)  # nosec
            return await self._send_response_request(settings)
        if self.ai_model_type == OpenAIModelTypes.EMBEDDING:
            assert isinstance(settings, OpenAIEmbeddingPromptExecutionSettings)  # nosec
            return await self._send_embedding_request(settings)
        if self.ai_model_type == OpenAIModelTypes.TEXT_TO_IMAGE:
            assert isinstance(settings, OpenAITextToImageExecutionSettings)  # nosec
            return await self._send_text_to_image_request(settings)
        if self.ai_model_type == OpenAIModelTypes.AUDIO_TO_TEXT:
            assert isinstance(settings, OpenAIAudioToTextExecutionSettings)  # nosec
            return await self._send_audio_to_text_request(settings)
        if self.ai_model_type == OpenAIModelTypes.TEXT_TO_AUDIO:
            assert isinstance(settings, OpenAITextToAudioExecutionSettings)  # nosec
            return await self._send_text_to_audio_request(settings)

        raise NotImplementedError(f"Model type {self.ai_model_type} is not supported")

    async def _send_response_request(self, settings: OpenAIResponseExecutionSettings) -> Response:
        """Send a request to the OpenAI response endpoint."""
        try:
            settings_dict = settings.prepare_settings_dict()
            response = await self.client.responses.create(**settings_dict)
            self.store_response_usage(response)
            return response
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to generate response",
                ex,
            ) from ex

    async def _send_completion_request(
        self,
        settings: OpenAIPromptExecutionSettings,
    ) -> ChatCompletion | Completion | AsyncStream[ChatCompletionChunk] | AsyncStream[Completion]:
        """Execute the appropriate call to OpenAI models."""
        try:
            settings_dict = settings.prepare_settings_dict()
            if self.ai_model_type == OpenAIModelTypes.CHAT:
                assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec
                self._handle_structured_output(settings, settings_dict)
                if settings.tools is None:
                    settings_dict.pop("parallel_tool_calls", None)
                response = await self.client.chat.completions.create(**settings_dict)
            else:
                response = await self.client.completions.create(**settings_dict)

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
        """Send a request to the OpenAI embeddings endpoint."""
        try:
            response = await self.client.embeddings.create(**settings.prepare_settings_dict())

            self.store_usage(response)
            return [x.embedding for x in response.data]
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to generate embeddings",
                ex,
            ) from ex

    async def _send_text_to_image_request(self, settings: OpenAITextToImageExecutionSettings) -> ImagesResponse:
        """Send a request to the OpenAI text to image endpoint."""
        try:
            return await self.client.images.generate(
                **settings.prepare_settings_dict(),
            )
        except Exception as ex:
            raise ServiceResponseException(f"Failed to generate image: {ex}") from ex

    async def _send_audio_to_text_request(self, settings: OpenAIAudioToTextExecutionSettings) -> Transcription:
        """Send a request to the OpenAI audio to text endpoint."""
        if not settings.filename:
            raise ServiceInvalidRequestError("Audio file is required for audio to text service")

        try:
            with open(settings.filename, "rb") as audio_file:
                return await self.client.audio.transcriptions.create(
                    file=audio_file,
                    **settings.prepare_settings_dict(),
                )
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to transcribe audio",
                ex,
            ) from ex

    async def _send_text_to_audio_request(
        self, settings: OpenAITextToAudioExecutionSettings
    ) -> _legacy_response.HttpxBinaryResponseContent:
        """Send a request to the OpenAI text to audio endpoint.

        The OpenAI API returns the content of the generated audio file.
        """
        try:
            return await self.client.audio.speech.create(
                **settings.prepare_settings_dict(),
            )
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to generate audio",
                ex,
            ) from ex

    def _handle_structured_output(
        self, request_settings: OpenAIChatPromptExecutionSettings, settings: dict[str, Any]
    ) -> None:
        response_format = getattr(request_settings, "response_format", None)
        if getattr(request_settings, "structured_json_response", False) and response_format:
            # Case 1: response_format is a type and subclass of BaseModel
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                settings["response_format"] = type_to_response_format_param(response_format)
            # Case 2: response_format is a type but not a subclass of BaseModel
            elif isinstance(response_format, type):
                generated_schema = KernelJsonSchemaBuilder.build(parameter_type=response_format, structured_output=True)
                assert generated_schema is not None  # nosec
                settings["response_format"] = generate_structured_output_response_format_schema(
                    name=response_format.__name__, schema=generated_schema
                )
            # Case 3: response_format is a dictionary, pass it without modification
            elif isinstance(response_format, dict):
                settings["response_format"] = response_format

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

    def store_response_usage(self, response: Response) -> None:
        """Retrieve and aggregate usage data from the response object.

        Tracking attributes (`prompt_tokens`, `completion_tokens`, `total_tokens`) and
        instantiate or update the `response_usage` model with the same data.
        """
        # 1. Ensure the response has a usage attribute and it's not empty.
        usage_data = getattr(response, "usage", None)
        if not usage_data:
            return  # No usage info to store

        # 2. Convert to dict if needed; handle both dict-like and Pydantic model usage structures.
        if not isinstance(usage_data, dict):
            # If `response.usage` is already a pydantic model, we can use `.dict()`.
            usage_data = usage_data.dict()

        # 3. Parse the raw usage data into our strongly-typed `ResponseUsage` model.
        usage_obj = ResponseUsage(**usage_data)

        # 4. Either set or update the handler's `response_usage`.
        if self.response_usage is None:
            self.response_usage = usage_obj
        else:
            # If you already have a `response_usage`, you could aggregate further
            # or overwrite, depending on your desired logic. Below is an example of
            # adding the token counts together if you wish to accumulate usage over time.
            self.response_usage.input_tokens += usage_obj.input_tokens
            self.response_usage.output_tokens += usage_obj.output_tokens
            self.response_usage.total_tokens += usage_obj.total_tokens
            self.response_usage.input_tokens_details.cached_tokens += usage_obj.input_tokens_details.cached_tokens
            self.response_usage.output_tokens_details.reasoning_tokens += (
                usage_obj.output_tokens_details.reasoning_tokens
            )

        # 5. Update the overarching usage counters in the handler.
        self.prompt_tokens += usage_obj.input_tokens
        self.completion_tokens += usage_obj.output_tokens
        self.total_tokens += usage_obj.total_tokens

        # 6. (Optional) Log the stored usage data with relevant details for traceability.
        logger.info(
            f"OpenAI usage stored. "
            f"Prompt tokens: {self.prompt_tokens}, "
            f"Completion tokens: {self.completion_tokens}, "
            f"Total tokens: {self.total_tokens}"
        )
