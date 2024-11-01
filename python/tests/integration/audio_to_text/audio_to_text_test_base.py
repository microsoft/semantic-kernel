# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.audio_to_text_client_base import AudioToTextClientBase
from semantic_kernel.connectors.ai.open_ai.services.azure_audio_to_text import AzureAudioToText
from semantic_kernel.connectors.ai.open_ai.services.open_ai_audio_to_text import OpenAIAudioToText


class AudioToTextTestBase:
    """Base class for testing audio-to-text services."""

    @pytest.fixture(scope="module")
    def services(self) -> dict[str, AudioToTextClientBase]:
        """Return audio-to-text services."""
        return {
            "openai": OpenAIAudioToText(),
            "azure_openai": AzureAudioToText(),
        }
