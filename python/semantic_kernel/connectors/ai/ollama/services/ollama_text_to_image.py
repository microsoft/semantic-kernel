# Copyright (c) Microsoft. All rights reserved.

import base64
import logging
import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from warnings import warn

from ollama import AsyncClient
from pydantic import ValidationError

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaTextToImagePromptExecutionSettings,
)
from semantic_kernel.connectors.ai.ollama.ollama_settings import OllamaSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_base import OllamaBase
from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class OllamaTextToImage(OllamaBase, TextToImageClientBase):
    """Ollama text to image client.

    Make sure to have the ollama service running either locally or remotely, with an
    image generation model pulled, for example `x/z-image-turbo`.
    """

    def __init__(
        self,
        service_id: str | None = None,
        ai_model_id: str | None = None,
        host: str | None = None,
        client: AsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an OllamaTextToImage service.

        Args:
            service_id (Optional[str]): Service ID tied to the execution settings. (Optional)
            ai_model_id (Optional[str]): The model name. (Optional)
            host (Optional[str]): URL of the Ollama server, defaults to None and
                will use the default Ollama service address: http://127.0.0.1:11434. (Optional)
            client (Optional[AsyncClient]): A custom Ollama client to use for the service. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
        """
        try:
            ollama_settings = OllamaSettings(
                image_model_id=ai_model_id,
                host=host,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Ollama settings.", ex) from ex

        if not ollama_settings.image_model_id:
            raise ServiceInitializationError("Ollama image model ID is not set.")

        super().__init__(
            service_id=service_id or ollama_settings.image_model_id,
            ai_model_id=ollama_settings.image_model_id,
            client=client or AsyncClient(host=ollama_settings.host),
        )

    @override
    async def generate_image(
        self,
        description: str,
        width: int | None = None,
        height: int | None = None,
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> bytes:
        """Generate an image from a text description.

        Args:
            description: Description of the image.
            width: Deprecated, use settings.width instead.
            height: Deprecated, use settings.height instead.
            settings: Execution settings for the prompt.
            kwargs: Additional arguments passed to the Ollama generate endpoint.

        Returns:
            bytes: The raw image bytes.
        """
        image_settings = (
            OllamaTextToImagePromptExecutionSettings()
            if settings is None
            else OllamaTextToImagePromptExecutionSettings.from_prompt_execution_settings(settings)
        )

        if width is not None:
            warn(
                "The 'width' argument is deprecated. Use 'settings.width' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if image_settings.width is None:
                image_settings.width = width
        if height is not None:
            warn(
                "The 'height' argument is deprecated. Use 'settings.height' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if image_settings.height is None:
                image_settings.height = height

        options = image_settings.prepare_settings_dict()
        options.update(kwargs)

        response_object = await self.client.generate(
            model=self.ai_model_id,
            prompt=description,
            stream=False,
            **options,
        )

        image = getattr(response_object, "image", None)
        if image is None and isinstance(response_object, Mapping):
            image = response_object.get("image")
        if not image:
            raise ServiceInvalidResponseError(
                "The Ollama response did not contain image data. Make sure the configured model "
                f"('{self.ai_model_id}') is an image generation model."
            )

        return base64.b64decode(image)

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OllamaTextToImagePromptExecutionSettings
