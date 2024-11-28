# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any

from openai.types.audio import Transcription

from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.audio_to_text_client_base import AudioToTextClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_audio_to_text_execution_settings import (
    OpenAIAudioToTextExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import AudioContent, TextContent


class OpenAIAudioToTextBase(OpenAIHandler, AudioToTextClientBase):
    """OpenAI audio to text client."""

    @override
    async def get_text_contents(
        self,
        audio_content: AudioContent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> list[TextContent]:
        if not settings:
            settings = OpenAIAudioToTextExecutionSettings(ai_model_id=self.ai_model_id)
        else:
            if not isinstance(settings, OpenAIAudioToTextExecutionSettings):
                settings = self.get_prompt_execution_settings_from_settings(settings)

        assert isinstance(settings, OpenAIAudioToTextExecutionSettings)  # nosec

        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id

        if not isinstance(audio_content.uri, str):
            raise ServiceInvalidRequestError("Audio content uri must be a string to a local file.")

        settings.filename = audio_content.uri

        response = await self._send_request(settings)
        assert isinstance(response, Transcription)  # nosec

        return [
            TextContent(
                ai_model_id=settings.ai_model_id,
                text=response.text,
                inner_content=response,
            )
        ]

    def get_prompt_execution_settings_class(self) -> type[PromptExecutionSettings]:
        """Get the request settings class."""
        return OpenAIAudioToTextExecutionSettings
