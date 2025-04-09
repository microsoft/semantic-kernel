# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.open_ai.services.azure_text_to_image import AzureTextToImage
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_to_image import OpenAITextToImage
from semantic_kernel.connectors.ai.text_to_image_client_base import TextToImageClientBase


class TextToImageTestBase:
    """Base class for testing text-to-image services."""

    @pytest.fixture(scope="module")
    def services(self) -> dict[str, TextToImageClientBase]:
        """Return text-to-image services."""
        return {
            "openai": OpenAITextToImage(),
            "azure_openai": AzureTextToImage(),
        }
