# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated, Any

from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel import Kernel


class ImageGenerationPlugin:
    """Class for image generation plugin."""

    def __init__(
        self,
        kernel: Kernel,
        service_id: str,
        default_width: int = 1024,
        default_height: int = 1024,
        generation_kwargs: dict[str, Any] | None = None,
    ):
        """Initialize the image generation plugin."""
        self.kernel = kernel
        self.service_id = service_id
        self.default_width = default_width
        self.default_height = default_height
        self.generation_kwargs = generation_kwargs or {}

    @kernel_function
    async def generate(
        self,
        description: Annotated[str, "Description of the image you want to generate."],
        width: Annotated[int | None, "The width of the image, optional."] = None,
        height: Annotated[int | None, "The height of the image, optional."] = None,
    ) -> ImageContent:
        """Generate a image based on a prompt."""
        service = self.kernel.get_service(self.service_id)
        if not service:
            raise ValueError(f"Service {self.service_id} not found.")
        width = width or self.default_width
        height = height or self.default_height
        assert isinstance(service, TextToImageClientBase)  # nosec
        image = await service.generate_image(
            description=description, width=width, height=height, **self.generation_kwargs
        )
        if isinstance(image, bytes):
            return ImageContent(data=image)
        return ImageContent(url=image)
