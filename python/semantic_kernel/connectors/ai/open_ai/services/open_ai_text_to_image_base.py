# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from openai.types.images_response import ImagesResponse

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_text_to_image_execution_settings import (
    ImageSize,
    OpenAITextToImageExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException


class OpenAITextToImageBase(OpenAIHandler, TextToImageClientBase):
    """OpenAI text to image client."""

    async def generate_image(self, description: str, width: int, height: int, **kwargs: Any) -> bytes | str:
        """Generate image from text.

        Args:
            description: Description of the image.
            width: Width of the image, check the openai documentation for the supported sizes.
            height: Height of the image, check the openai documentation for the supported sizes.
            kwargs: Additional arguments, check the openai images.generate documentation for the supported arguments.

        Returns:
            bytes | str: Image bytes or image URL.
        """
        settings = OpenAITextToImageExecutionSettings(
            prompt=description,
            size=ImageSize(width=width, height=height),
            ai_model_id=self.ai_model_id,
            **kwargs,
        )

        response = await self._send_request(settings)

        assert isinstance(response, ImagesResponse)  # nosec
        if not response.data or not response.data[0].url:
            raise ServiceResponseException("Failed to generate image.")

        return response.data[0].url

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Get the request settings class."""
        return OpenAITextToImageExecutionSettings
