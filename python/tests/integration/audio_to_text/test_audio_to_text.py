# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

from semantic_kernel.connectors.ai.audio_to_text_client_base import AudioToTextClientBase
from semantic_kernel.contents import AudioContent
from tests.integration.audio_to_text.audio_to_text_test_base import AudioToTextTestBase, azure_setup

pytestmark = pytest.mark.parametrize(
    "service_id, audio_content, expected_text",
    [
        pytest.param(
            "openai",
            AudioContent.from_audio_file(os.path.join(os.path.dirname(__file__), "../../", "assets/sample_audio.mp3")),
            ["hi", "how", "are", "you", "doing"],
            id="openai",
        ),
        pytest.param(
            "azure_openai",
            AudioContent.from_audio_file(os.path.join(os.path.dirname(__file__), "../../", "assets/sample_audio.mp3")),
            ["hi", "how", "are", "you", "doing"],
            marks=pytest.mark.skipif(not azure_setup, reason="Azure Audio to Text not setup."),
            id="azure_openai",
        ),
    ],
)


class TestAudioToText(AudioToTextTestBase):
    """Test audio-to-text services."""

    async def test_audio_to_text(
        self,
        services: dict[str, AudioToTextClientBase],
        service_id: str,
        audio_content: AudioContent,
        expected_text: list[str],
    ) -> None:
        """Test audio-to-text services.

        Args:
            services: Audio-to-text services.
            service_id: Service ID.
            audio_content: Audio content.
            expected_text: Expected text, list of words.
        """

        service = services[service_id]
        if not service:
            pytest.mark.xfail("Azure Audio to Text not setup.")
        result = await service.get_text_content(audio_content)

        for word in expected_text:
            assert word in result.text.lower(), (
                f"Expected word '{word}' not found in result text: {result.text.lower()}"
            )
