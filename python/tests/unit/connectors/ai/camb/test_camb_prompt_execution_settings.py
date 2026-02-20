# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.camb.camb_prompt_execution_settings import (
    CambAudioToTextExecutionSettings,
    CambTextToAudioExecutionSettings,
)


def test_tts_settings_defaults():
    settings = CambTextToAudioExecutionSettings()
    assert settings.voice_id is None
    assert settings.language is None
    assert settings.output_format is None
    assert settings.user_instructions is None


def test_tts_settings_custom_values():
    settings = CambTextToAudioExecutionSettings(
        voice_id=147320,
        language="en-us",
        output_format="wav",
        user_instructions="Speak slowly and clearly.",
    )
    assert settings.voice_id == 147320
    assert settings.language == "en-us"
    assert settings.output_format == "wav"
    assert settings.user_instructions == "Speak slowly and clearly."


def test_tts_settings_invalid_output_format():
    with pytest.raises(ValidationError):
        CambTextToAudioExecutionSettings(output_format="invalid_format")


def test_tts_settings_user_instructions_too_long():
    with pytest.raises(ValidationError):
        CambTextToAudioExecutionSettings(user_instructions="x" * 1001)


def test_stt_settings_defaults():
    settings = CambAudioToTextExecutionSettings()
    assert settings.language is None


def test_stt_settings_custom_values():
    settings = CambAudioToTextExecutionSettings(language=1)
    assert settings.language == 1
