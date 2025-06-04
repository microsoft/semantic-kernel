# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

from semantic_kernel.connectors.ai.audio_to_text_client_base import AudioToTextClientBase
from semantic_kernel.connectors.ai.open_ai import AzureAudioToText, OpenAIAudioToText
from tests.utils import is_service_setup_for_testing

# There is only the whisper model available on Azure OpenAI for audio to text. And that model is
# only available in the North Switzerland region. Therefore, the endpoint is different than the one
# we use for other services.
azure_setup = is_service_setup_for_testing(["AZURE_OPENAI_AUDIO_TO_TEXT_ENDPOINT"])


class AudioToTextTestBase:
    """Base class for testing audio-to-text services."""

    @pytest.fixture(scope="module")
    def services(self) -> dict[str, AudioToTextClientBase]:
        """Return audio-to-text services."""
        return {
            "openai": OpenAIAudioToText(),
            "azure_openai": AzureAudioToText(endpoint=os.environ["AZURE_OPENAI_AUDIO_TO_TEXT_ENDPOINT"])
            if azure_setup
            else None,
        }
