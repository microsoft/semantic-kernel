# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TYPE_CHECKING, Any, Union

from numpy import array, ndarray

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.voyage_ai.services.voyage_ai_base import VoyageAIBase
from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_prompt_execution_settings import (
    VoyageAIMultimodalEmbeddingPromptExecutionSettings,
)
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceResponseException,
)

if TYPE_CHECKING:
    from PIL.Image import Image

    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class VoyageAIMultimodalEmbedding(VoyageAIBase, EmbeddingGeneratorBase):
    """VoyageAI Multimodal Embedding Service.

    Generates embeddings for text, images, or interleaved text and images.
    Supports the voyage-multimodal-3 model.

    Constraints:
    - Maximum 1,000 inputs per request
    - Images: ≤16 million pixels, ≤20 MB
    - Total tokens per input: ≤32,000 (560 pixels = 1 token)
    - Aggregate tokens across inputs: ≤320,000
    """

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
        env_file_path: str | None = None,
        endpoint: str | None = None,
    ):
        """Initialize VoyageAI multimodal embedding service.

        Args:
            ai_model_id: The VoyageAI model ID (required).
            service_id: The service ID (optional).
            api_key: The VoyageAI API key (optional).
            client: A pre-configured VoyageAI client (optional).
            env_file_path: Path to .env file (optional).
            endpoint: VoyageAI API endpoint (optional).
        """
        # Use multimodal model from settings if not provided
        if not ai_model_id:
            from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_settings import VoyageAISettings

            settings = VoyageAISettings.create(env_file_path=env_file_path)
            ai_model_id = settings.multimodal_embedding_model_id

        if not ai_model_id:
            raise ServiceInitializationError(
                "No model ID provided. Set ai_model_id parameter or "
                "VOYAGE_AI_MULTIMODAL_EMBEDDING_MODEL_ID environment variable."
            )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id,
            api_key=api_key,
            client=client,
            env_file_path=env_file_path,
            endpoint=endpoint,
        )

    async def generate_multimodal_embeddings(
        self,
        inputs: list[Union[str, "Image", list[Union[str, "Image"]]]],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        """Generate multimodal embeddings for text and/or images.

        Args:
            inputs: List of inputs. Each input can be:
                   - A string (text)
                   - A PIL Image object
                   - A list containing text strings and/or PIL Images (interleaved)
            settings: Prompt execution settings (optional).
            kwargs: Additional arguments to pass to the request.

        Returns:
            ndarray: Array of multimodal embeddings.

        Example:
            ```python
            from PIL import Image

            # Text only
            embeddings = await service.generate_multimodal_embeddings(["Text description of image"])

            # Image only
            img = Image.open("photo.jpg")
            embeddings = await service.generate_multimodal_embeddings([img])

            # Interleaved text and images
            embeddings = await service.generate_multimodal_embeddings([
                ["Chapter 1: Introduction", img1, "This shows...", img2]
            ])
            ```
        """
        if not settings:
            settings = VoyageAIMultimodalEmbeddingPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)

        try:
            # Call VoyageAI multimodal embeddings API
            response = await self.aclient.multimodal_embed(
                inputs=inputs,
                model=self.ai_model_id,
                **settings.prepare_settings_dict(),
            )

            # Extract embeddings
            embeddings = response.embeddings
            return array(embeddings)

        except Exception as e:
            raise ServiceResponseException(f"VoyageAI multimodal embedding request failed: {e}") from e

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        """Generate embeddings for text inputs.

        This method converts text-only inputs to multimodal format.

        Args:
            texts: List of text strings to generate embeddings for.
            settings: Prompt execution settings (optional).
            kwargs: Additional arguments to pass to the request.

        Returns:
            ndarray: Array of embeddings.
        """
        # Convert each text to a single-item list (required by VoyageAI multimodal API)
        multimodal_inputs = [[text] for text in texts]
        return await self.generate_multimodal_embeddings(multimodal_inputs, settings, **kwargs)

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the prompt execution settings class."""
        return VoyageAIMultimodalEmbeddingPromptExecutionSettings
