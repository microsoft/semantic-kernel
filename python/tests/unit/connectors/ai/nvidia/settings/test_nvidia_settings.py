# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.nvidia.settings.nvidia_settings import NvidiaSettings


class TestNvidiaSettings:
    """Test cases for NvidiaSettings."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        settings = NvidiaSettings()
        assert settings.api_key is None
        assert settings.base_url == "https://integrate.api.nvidia.com/v1"
        assert settings.embedding_model_id is None
        assert settings.chat_model_id is None

    def test_init_with_values(self):
        """Test initialization with specific values."""
        settings = NvidiaSettings(
            api_key="test-api-key",
            base_url="https://custom.nvidia.com/v1",
            embedding_model_id="test-embedding-model",
            chat_model_id="test-chat-model",
        )

        assert settings.api_key.get_secret_value() == "test-api-key"
        assert settings.base_url == "https://custom.nvidia.com/v1"
        assert settings.embedding_model_id == "test-embedding-model"
        assert settings.chat_model_id == "test-chat-model"

    def test_env_prefix(self):
        """Test environment variable prefix."""
        assert NvidiaSettings.env_prefix == "NVIDIA_"

    def test_api_key_secret_str(self):
        """Test that api_key is properly handled as SecretStr."""
        settings = NvidiaSettings(api_key="secret-key")

        # Should be SecretStr type
        assert hasattr(settings.api_key, "get_secret_value")
        assert settings.api_key.get_secret_value() == "secret-key"

        # Should not expose the secret in string representation
        str_repr = str(settings)
        assert "secret-key" not in str_repr

    def test_environment_variables(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("NVIDIA_API_KEY", "env-key")
        monkeypatch.setenv("NVIDIA_CHAT_MODEL_ID", "env-chat")

        settings = NvidiaSettings()

        assert settings.api_key.get_secret_value() == "env-key"
        assert settings.chat_model_id == "env-chat"
