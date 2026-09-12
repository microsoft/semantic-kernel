# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_prompt_execution_settings import (
    MiniMaxChatPromptExecutionSettings,
    MiniMaxPromptExecutionSettings,
)


class TestMiniMaxPromptExecutionSettings:
    """Test cases for MiniMaxPromptExecutionSettings."""

    def test_default_init(self):
        """Test default initialization."""
        settings = MiniMaxChatPromptExecutionSettings()
        assert settings.temperature is None
        assert settings.stream is False

    def test_prepare_settings_dict(self):
        """Test that prepare_settings_dict serializes with model alias."""
        settings = MiniMaxChatPromptExecutionSettings(
            messages=[{"role": "user", "content": "Hello"}],
            ai_model_id="MiniMax-M3",
            temperature=0.5,
        )
        result = settings.prepare_settings_dict()
        assert result["model"] == "MiniMax-M3"
        assert result["temperature"] == 0.5
        assert result["messages"] == [{"role": "user", "content": "Hello"}]
        assert "response_format" not in result
        assert "service_id" not in result

    @pytest.mark.parametrize("temperature", [0.0, 0.5, 1.0])
    def test_temperature_valid_range(self, temperature):
        """Test that valid temperatures are accepted."""
        settings = MiniMaxChatPromptExecutionSettings(temperature=temperature)
        assert settings.temperature == temperature

    @pytest.mark.parametrize("temperature", [-0.1, 1.1, 2.0])
    def test_temperature_invalid_range(self, temperature):
        """Test that out-of-range temperatures are rejected."""
        with pytest.raises(ValueError):
            MiniMaxChatPromptExecutionSettings(temperature=temperature)

    def test_base_prompt_execution_settings(self):
        """Test the base prompt execution settings."""
        settings = MiniMaxPromptExecutionSettings()
        assert settings.format is None
        assert settings.options is None
