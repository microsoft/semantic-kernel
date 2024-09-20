# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
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
        try:
            result = await self.client.images.generate(
                prompt=description,
                model=self.ai_model_id,
                size=f"{width}x{height}",  # type: ignore
                response_format="url",
                **kwargs,
            )
        except Exception as ex:
            raise ServiceResponseException(f"Failed to generate image: {ex}") from ex
        if not result.data or not result.data[0].url:
            raise ServiceResponseException("Failed to generate image.")
        return result.data[0].url
