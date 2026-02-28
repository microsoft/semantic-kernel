# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.camb.camb_plugin import CambPlugin
from semantic_kernel.connectors.ai.camb.camb_prompt_execution_settings import (
    CambAudioToTextExecutionSettings,
    CambTextToAudioExecutionSettings,
)
from semantic_kernel.connectors.ai.camb.services.camb_audio_to_text import CambAudioToText
from semantic_kernel.connectors.ai.camb.services.camb_text_to_audio import CambTextToAudio

__all__ = [
    "CambAudioToText",
    "CambAudioToTextExecutionSettings",
    "CambPlugin",
    "CambTextToAudio",
    "CambTextToAudioExecutionSettings",
]
