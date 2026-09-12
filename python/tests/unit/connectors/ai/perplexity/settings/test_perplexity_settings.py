# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.perplexity.settings.perplexity_settings import PerplexitySettings


class TestPerplexitySettings:
    """Test cases for PerplexitySettings."""

    def test_init_with_defaults(self):
        """Test initialization uses documented defaults."""
        settings = PerplexitySettings()
        assert settings.api_key is None
        assert settings.chat_model_id == "sonar-pro"
        assert settings.base_url == "https://api.perplexity.ai"

    def test_init_with_values(self):
        """Test initialization with explicit values."""
        settings = PerplexitySettings(
            api_key="test-api-key",
            chat_model_id="sonar-pro",
            base_url="https://example.test/api",
        )

        assert settings.api_key.get_secret_value() == "test-api-key"
        assert settings.chat_model_id == "sonar-pro"
        assert settings.base_url == "https://example.test/api"

    def test_loads_from_env(self, monkeypatch):
        """Settings should pick up values from PERPLEXITY_* env vars."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "env-api-key")
        monkeypatch.setenv("PERPLEXITY_CHAT_MODEL_ID", "sonar-pro")

        settings = PerplexitySettings()

        assert settings.api_key.get_secret_value() == "env-api-key"
        assert settings.chat_model_id == "sonar-pro"
