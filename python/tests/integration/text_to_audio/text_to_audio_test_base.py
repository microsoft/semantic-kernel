# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

from semantic_kernel.connectors.ai.open_ai import AzureTextToAudio, OpenAITextToAudio
from semantic_kernel.connectors.ai.text_to_audio_client_base import TextToAudioClientBase
from tests.utils import is_service_setup_for_testing

# TTS model on Azure model is not available in regions at which we have chat completion models.
# Therefore, we need to use a different endpoint for testing.
azure_setup = is_service_setup_for_testing(["AZURE_OPENAI_TEXT_TO_AUDIO_ENDPOINT"])


class TextToAudioTestBase:
    """Base class for testing text-to-audio services."""

    @pytest.fixture(scope="module")
    def services(self) -> dict[str, TextToAudioClientBase]:
        """Return text-to-audio services."""
        return {
            "openai": OpenAITextToAudio(),
            "azure_openai": AzureTextToAudio(endpoint=os.environ["AZURE_OPENAI_TEXT_TO_AUDIO_ENDPOINT"])
            if azure_setup
            else None,
        }
