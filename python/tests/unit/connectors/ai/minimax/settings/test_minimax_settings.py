# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.minimax.settings.minimax_settings import MiniMaxSettings


class TestMiniMaxSettings:
    """Test cases for MiniMaxSettings."""

    def test_init_with_defaults(self, minimax_unit_test_env):
        """Test initialization with default values."""
        settings = MiniMaxSettings()
        assert settings.api_key.get_secret_value() == "test_api_key"
        assert settings.region == "global_en"
        assert settings.base_url == "https://api.minimax.io/v1"
        assert settings.chat_model_id == "MiniMax-M3"

    def test_init_with_values(self):
        """Test initialization with specific values."""
        settings = MiniMaxSettings(
            api_key="test-api-key",
            base_url="https://custom.minimax.io/v1",
            region="cn_zh",
            chat_model_id="MiniMax-M2.7",
        )

        assert settings.api_key.get_secret_value() == "test-api-key"
        assert settings.base_url == "https://custom.minimax.io/v1"
        assert settings.region == "cn_zh"
        assert settings.chat_model_id == "MiniMax-M2.7"

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

    def test_region_resolves_global_base_url(self, minimax_unit_test_env):
        """Test that the global region resolves the global base URL."""
        settings = MiniMaxSettings()
        assert settings.base_url == "https://api.minimax.io/v1"

    @pytest.mark.parametrize("override_env_param_dict", [{"MINIMAX_REGION": "cn_zh"}], indirect=True)
    def test_region_cn_resolves_cn_base_url(self, minimax_unit_test_env):
        """Test that the China region resolves the China base URL."""
        settings = MiniMaxSettings()
        assert settings.region == "cn_zh"
        assert settings.base_url == "https://api.minimaxi.com/v1"

    def test_explicit_base_url_overrides_region(self, minimax_unit_test_env):
        """Test that an explicit base_url overrides the region-derived URL."""
        settings = MiniMaxSettings(base_url="https://custom.minimax.io/v1", region="cn_zh")
        assert settings.base_url == "https://custom.minimax.io/v1"
