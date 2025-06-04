# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.text_to_audio_client_base import TextToAudioClientBase
from semantic_kernel.contents import AudioContent
from tests.integration.text_to_audio.text_to_audio_test_base import TextToAudioTestBase, azure_setup

pytestmark = pytest.mark.parametrize(
    "service_id, text",
    [
        pytest.param(
            "openai",
            "Hello World!",
            id="openai",
        ),
        pytest.param(
            "azure_openai",
            "Hello World!",
            marks=pytest.mark.skipif(not azure_setup, reason="Azure Audio to Text not setup."),
            id="azure_openai",
        ),
    ],
)


class TestTextToAudio(TextToAudioTestBase):
    """Test text-to-audio services."""

    async def test_audio_to_text(
        self,
        services: dict[str, TextToAudioClientBase],
        service_id: str,
        text: str,
    ) -> None:
        """Test text-to-audio services.

        Args:
            services: text-to-audio services.
            service_id: Service ID.
            text: Text content.
        """

        service = services[service_id]
        result = await service.get_audio_content(text)

        assert isinstance(result, AudioContent)
        assert result.data is not None
