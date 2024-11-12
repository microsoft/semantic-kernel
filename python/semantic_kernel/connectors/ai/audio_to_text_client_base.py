# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class AudioToTextClientBase(AIServiceClientBase, ABC):
    """Base class for audio to text client."""

    @abstractmethod
    async def get_text_contents(
        self,
        audio_content: AudioContent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[TextContent]:
        """Get text contents from audio.

        Args:
            audio_content: Audio content.
            settings: Prompt execution settings.
            kwargs: Additional arguments.

        Returns:
            list[TextContent]: Text contents.
        """
        raise NotImplementedError

    async def get_text_content(
        self,
        audio_content: AudioContent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> TextContent:
        """Get text content from audio.

        Args:
            audio_content: Audio content.
            settings: Prompt execution settings.
            kwargs: Additional arguments.

        Returns:
            TextContent: Text content.
        """
        return (await self.get_text_contents(audio_content, settings, **kwargs))[0]
