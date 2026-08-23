# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.minimax import MiniMaxTextToAudio, MiniMaxTextToAudioExecutionSettings


def test_text_to_audio_settings_prepare_request() -> None:
    settings = MiniMaxTextToAudioExecutionSettings(
        ai_model_id="speech-2.8-hd",
        input="Hello",
        output_format="mp3",
        audio_setting={"sample_rate": 32000},
    )

    assert settings.prepare_settings_dict() == {
        "model": "speech-2.8-hd",
        "text": "Hello",
        "output_format": "mp3",
        "audio_setting": {"sample_rate": 32000},
    }


def test_text_to_audio_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key")
    monkeypatch.setenv("MINIMAX_TEXT_TO_AUDIO_MODEL_ID", "speech-2.8-hd")

    service = MiniMaxTextToAudio()

    assert service.ai_model_id == "speech-2.8-hd"
    assert service.base_url == "https://api.minimax.io/v1/t2a_v2"
    assert service.get_prompt_execution_settings_class() is MiniMaxTextToAudioExecutionSettings
