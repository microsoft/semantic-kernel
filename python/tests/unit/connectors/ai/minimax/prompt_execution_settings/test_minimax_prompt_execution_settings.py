# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_prompt_execution_settings import (
    MiniMaxChatPromptExecutionSettings,
)


class TestMiniMaxChatPromptExecutionSettings:
    """Test cases for MiniMaxChatPromptExecutionSettings."""

    def test_default_settings(self):
        """Test default settings initialization."""
        settings = MiniMaxChatPromptExecutionSettings()
        assert settings.temperature is None
        assert settings.top_p is None
        assert settings.max_tokens is None
        assert settings.stream is False

    def test_settings_with_values(self):
        """Test settings with specific values."""
        settings = MiniMaxChatPromptExecutionSettings(
            temperature=0.7,
            top_p=0.9,
            max_tokens=1000,
        )
        assert settings.temperature == 0.7
        assert settings.top_p == 0.9
        assert settings.max_tokens == 1000

    def test_prepare_settings_dict(self):
        """Test prepare_settings_dict excludes correct fields."""
        settings = MiniMaxChatPromptExecutionSettings(
            temperature=0.7,
            max_tokens=100,
            service_id="test-service",
        )
        result = settings.prepare_settings_dict()
        assert "temperature" in result
        assert "max_tokens" in result
        assert "service_id" not in result
        assert "response_format" not in result

    def test_model_alias(self):
        """Test that ai_model_id serializes as 'model'."""
        settings = MiniMaxChatPromptExecutionSettings(ai_model_id="MiniMax-M2.7")
        result = settings.prepare_settings_dict()
        assert "model" in result
        assert result["model"] == "MiniMax-M2.7"
