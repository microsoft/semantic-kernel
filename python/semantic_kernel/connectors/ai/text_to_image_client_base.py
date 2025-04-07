# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class TextToImageClientBase(AIServiceClientBase, ABC):
    """Base class for text to image client."""

    @abstractmethod
    async def generate_image(self, prompt: str, settings: PromptExecutionSettings, **kwargs: Any) -> bytes | str:
        """Generate image from text.

        Args:
            prompt: Description of the image.
            settings: Execution settings for the prompt.
            kwargs: Additional arguments.

        Returns:
            bytes | str: Image bytes or image URL.
        """
        raise NotImplementedError

    async def get_image_content(self, prompt: str, settings: PromptExecutionSettings, **kwargs: Any) -> ImageContent:
        """Get image content.

        Args:
            prompt: Description of the image.
            settings: Execution settings for the prompt.
            kwargs: Additional arguments.

        Returns:
            ImageContent: Image content.
        """
        image = await self.generate_image(prompt, settings, **kwargs)
        if isinstance(image, str):
            return ImageContent(uri=image)
        return ImageContent(data=image)
