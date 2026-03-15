# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.minimax.settings.minimax_settings import MiniMaxSettings


class TestMiniMaxSettings:
    """Test cases for MiniMaxSettings."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = MiniMaxSettings()
        assert settings.api_key is None
        assert settings.base_url == "https://api.minimax.io/v1"
        assert settings.chat_model_id is None

    def test_init_with_values(self):
        """Test initialization with specific values."""
        settings = MiniMaxSettings(
            api_key="test-api-key",
            base_url="https://custom.minimax.io/v1",
            chat_model_id="MiniMax-M2.5",
        )

        assert settings.api_key.get_secret_value() == "test-api-key"
        assert settings.base_url == "https://custom.minimax.io/v1"
        assert settings.chat_model_id == "MiniMax-M2.5"

    def test_env_prefix(self):
        """Test environment variable prefix."""
        assert MiniMaxSettings.env_prefix == "MINIMAX_"

    def test_api_key_secret_str(self):
        """Test that api_key is properly handled as SecretStr."""
        settings = MiniMaxSettings(api_key="secret-key")

        assert hasattr(settings.api_key, "get_secret_value")
        assert settings.api_key.get_secret_value() == "secret-key"

        str_repr = str(settings)
        assert "secret-key" not in str_repr

    def test_environment_variables(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("MINIMAX_API_KEY", "env-key")
        monkeypatch.setenv("MINIMAX_CHAT_MODEL_ID", "MiniMax-M2.5")

        settings = MiniMaxSettings()

        assert settings.api_key.get_secret_value() == "env-key"
        assert settings.chat_model_id == "MiniMax-M2.5"
