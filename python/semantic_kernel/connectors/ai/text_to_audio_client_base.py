# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class TextToAudioClientBase(AIServiceClientBase, ABC):
    """Base class for text to audio client."""

    @abstractmethod
    async def get_audio_contents(
        self,
        text: str,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[AudioContent]:
        """Get audio contents from text.

        Args:
            text: The text to convert to audio.
            settings: Prompt execution settings.
            kwargs: Additional arguments.

        Returns:
            list[AudioContent]: The generated audio contents.

            Some services may return multiple audio contents in one call. some services don't.
            It is ok to return a list of one element.
        """
        raise NotImplementedError

    async def get_audio_content(
        self,
        text: str,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> AudioContent:
        """Get audio content from text.

        Args:
            text: The text to convert to audio.
            settings: Prompt execution settings.
            kwargs: Additional arguments.

        Returns:
            AudioContent: The generated audio content.
        """
        return (await self.get_audio_contents(text, settings, **kwargs))[0]
