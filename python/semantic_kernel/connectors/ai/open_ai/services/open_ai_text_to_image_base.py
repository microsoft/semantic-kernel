# Copyright (c) Microsoft. All rights reserved.

from typing import Any
from warnings import warn

from openai.types.images_response import ImagesResponse

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_text_to_image_execution_settings import (
    ImageSize,
    OpenAITextToImageExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError, ServiceResponseException


class OpenAITextToImageBase(OpenAIHandler, TextToImageClientBase):
    """OpenAI text to image client."""

    async def generate_image(
        self,
        description: str,
        width: int | None = None,
        height: int | None = None,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> bytes | str:
        """Generate image from text.

        Args:
            description: Description of the image.
            width: Deprecated, use settings instead.
            height: Deprecated, use settings instead.
            settings: Execution settings for the prompt.
            kwargs: Additional arguments, check the openai images.generate documentation for the supported arguments.

        Returns:
            bytes | str: Image bytes or image URL.
        """
        if not settings:
            settings = OpenAITextToImageExecutionSettings(**kwargs)
        if not isinstance(settings, OpenAITextToImageExecutionSettings):
            settings = OpenAITextToImageExecutionSettings.from_prompt_execution_settings(settings)
        if width:
            warn("The 'width' argument is deprecated. Use 'settings.size' instead.", DeprecationWarning)
            if settings.size and not settings.size.width:
                settings.size.width = width
        if height:
            warn("The 'height' argument is deprecated. Use 'settings.size' instead.", DeprecationWarning)
            if settings.size and not settings.size.height:
                settings.size.height = height
        if not settings.size and width and height:
            settings.size = ImageSize(width=width, height=height)

        if not settings.prompt:
            settings.prompt = description

        if not settings.prompt:
            raise ServiceInvalidRequestError("Prompt is required.")

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        response = await self._send_request(settings)

        assert isinstance(response, ImagesResponse)  # nosec
        if not response.data or not response.data[0].url:
            raise ServiceResponseException("Failed to generate image.")

        return response.data[0].url

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Get the request settings class."""
        return OpenAITextToImageExecutionSettings
