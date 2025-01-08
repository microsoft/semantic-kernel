# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


class RealtimeClientBase(AIServiceClientBase, ABC):
    """Base class for audio to text client."""

    @abstractmethod
    async def receive(
        self,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[TextContent | AudioContent, Any]:
        """Get text contents from audio.

        Args:
            settings: Prompt execution settings.
            kwargs: Additional arguments.

        Returns:
            list[TextContent | AudioContent]: response contents.
        """
        raise NotImplementedError

    @abstractmethod
    async def send(
        self,
        audio_content: AudioContent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> None:
        """Get text content from audio.

        Args:
            audio_content: Audio content.
            settings: Prompt execution settings.
            kwargs: Additional arguments.

        Returns:
            TextContent: Text content.
        """
        raise NotImplementedError
