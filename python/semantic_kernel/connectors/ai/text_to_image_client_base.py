# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import Any

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class TextToImageClientBase(AIServiceClientBase, ABC):
    """Base class for text to image client."""

    @abstractmethod
    async def generate_image(self, description: str, width: int, height: int, **kwargs: Any) -> bytes | str:
        """Generate image from text.

        Args:
            description: Description of the image.
            width: Width of the image.
            height: Height of the image.
            kwargs: Additional arguments.

        Returns:
            bytes | str: Image bytes or image URL.
        """
        raise NotImplementedError
