# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_text_to_audio_execution_settings import (
    MiniMaxTextToAudioExecutionSettings,
)
from semantic_kernel.connectors.ai.minimax.services.minimax_text_to_audio import MiniMaxTextToAudio
from semantic_kernel.connectors.ai.minimax.settings.minimax_settings import MiniMaxSettings

__all__ = ["MiniMaxSettings", "MiniMaxTextToAudio", "MiniMaxTextToAudioExecutionSettings"]
