# Copyright (c) Microsoft. All rights reserved.

from pathlib import Path
from typing import IO, Any
from warnings import warn

from openai._types import FileTypes, Omit, omit
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
        warn("generate_image is deprecated. Use generate_images.", DeprecationWarning, stacklevel=2)
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

    async def generate_images(
        self,
        prompt: str,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Generate one or more images from text. Returns URLs or base64-encoded images.

        Args:
            prompt: Description of the image(s) to generate.
            settings: Execution settings for the prompt.
            kwargs: Additional arguments, check the openai images.generate documentation for the supported arguments.

        Returns:
            list[str]: Image URLs or base64-encoded images.

        Example:
            Generate images and save them as PNG files:

            ```python
            from semantic_kernel.connectors.ai.open_ai import AzureTextToImage
            import base64, os

            service = AzureTextToImage(
                service_id="image1",
                deployment_name="gpt-image-1",
                endpoint="https://your-endpoint.cognitiveservices.azure.com",
                api_key="your-api-key",
                api_version="2025-04-01-preview",
            )
            settings = service.get_prompt_execution_settings_class()(service_id="image1")
            settings.n = 3
            images_b64 = await service.generate_images("A cute cat wearing a whimsical striped hat", settings=settings)
            ```
        """
        if not settings:
            settings = OpenAITextToImageExecutionSettings(**kwargs)
        if not isinstance(settings, OpenAITextToImageExecutionSettings):
            settings = OpenAITextToImageExecutionSettings.from_prompt_execution_settings(settings)
        if prompt:
            settings.prompt = prompt

        if not settings.prompt:
            raise ServiceInvalidRequestError("Prompt is required.")

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        response = await self._send_request(settings)

        assert isinstance(response, ImagesResponse)  # nosec
        if not response.data or not isinstance(response.data, list) or len(response.data) == 0:
            raise ServiceResponseException("Failed to generate image.")

        results: list[str] = []
        for image in response.data:
            url: str | None = getattr(image, "url", None)
            b64_json: str | None = getattr(image, "b64_json", None)
            if url:
                results.append(url)
            elif b64_json:
                results.append(b64_json)
            else:
                continue

        if len(results) == 0:
            raise ServiceResponseException("No valid image data found in response.")
        return results

    async def edit_image(
        self,
        prompt: str,
        image_paths: list[str] | None = None,
        image_files: list[IO[bytes]] | None = None,
        mask_path: str | None = None,
        mask_file: IO[bytes] | None = None,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Edit images using the OpenAI image edit API.

        Args:
            prompt: Instructional prompt for image editing.
            image_paths: List of image file paths to edit.
            image_files: List of file-like objects (opened in binary mode) to edit.
            mask_path: Optional mask image file path.
            mask_file: Optional mask image file-like object (opened in binary mode).
            settings: Optional execution settings. If not provided, will be constructed from kwargs.
            kwargs: Additional API parameters.

        Returns:
            list[str]: List of edited image URLs or base64-encoded strings.

        Example:
            Edit images from file path and save results:

            ```python
            from semantic_kernel.connectors.ai.open_ai import AzureTextToImage
            import base64, os

            service = AzureTextToImage(
                service_id="image1",
                deployment_name="gpt-image-1",
                endpoint="https://your-endpoint.cognitiveservices.azure.com",
                api_key="your-api-key",
                api_version="2025-04-01-preview",
            )
            file_paths = ["./new_images/img_1.png", "./new_images/img_2.png"]
            settings = service.get_prompt_execution_settings_class()(service_id="image1")
            settings.n = 2
            results = await service.edit_image(
                prompt="Make the cat wear a wizard hat",
                image_paths=file_paths,
                settings=settings,
            )
            ```

            Edit images from file object:

            ```python
            with open("./new_images/img_1.png", "rb") as f:
                results = await service.edit_image(
                    prompt="Make the cat wear a wizard hat",
                    image_files=[f],
                )
            ```
        """
        if not settings:
            settings = OpenAITextToImageExecutionSettings(**kwargs)
        if not isinstance(settings, OpenAITextToImageExecutionSettings):
            settings = OpenAITextToImageExecutionSettings.from_prompt_execution_settings(settings)
        settings.prompt = prompt

        if not settings.prompt:
            raise ServiceInvalidRequestError("Prompt is required.")
        if (image_paths is None and image_files is None) or (image_paths is not None and image_files is not None):
            raise ServiceInvalidRequestError("Provide either 'image_paths' or 'image_files', and only one.")

        images: list[FileTypes] = []
        if image_paths is not None:
            images = [Path(p) for p in image_paths]
        elif image_files is not None:
            images = list(image_files)

        mask: FileTypes | Omit = omit
        if mask_path is not None:
            mask = Path(mask_path)
        elif mask_file is not None:
            mask = mask_file

        response: ImagesResponse = await self._send_image_edit_request(
            image=images,
            mask=mask,
            settings=settings,
        )

        if not response or not response.data or not isinstance(response.data, list):
            raise ServiceResponseException("Failed to edit image.")

        results: list[str] = []
        for img in response.data:
            b64_json: str | None = getattr(img, "b64_json", None)
            url: str | None = getattr(img, "url", None)
            if b64_json:
                results.append(b64_json)
            elif url:
                results.append(url)
        if not results:
            raise ServiceResponseException("No valid image data found in response.")
        return results

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Get the request settings class."""
        return OpenAITextToImageExecutionSettings
