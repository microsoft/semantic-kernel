# Copyright (c) Microsoft. All rights reserved.

"""Unit tests for ModelsLabChatCompletion."""

import os
from unittest.mock import MagicMock, patch

import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.modelslab import (
    MODELSLAB_CHAT_BASE_URL,
    MODELSLAB_CHAT_MODELS,
    MODELSLAB_DEFAULT_CHAT_MODEL,
    ModelsLabChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(**kwargs) -> ModelsLabChatCompletion:
    """Return a ModelsLabChatCompletion backed by a mock AsyncOpenAI client."""
    mock_client = MagicMock(spec=AsyncOpenAI)
    return ModelsLabChatCompletion(async_client=mock_client, **kwargs)


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------

class TestInheritance:
    def test_is_open_ai_chat_completion_subclass(self):
        """ModelsLabChatCompletion must inherit from OpenAIChatCompletion."""
        assert issubclass(ModelsLabChatCompletion, OpenAIChatCompletion)

    def test_instance_is_open_ai_chat_completion(self):
        svc = _make_service()
        assert isinstance(svc, OpenAIChatCompletion)


# ---------------------------------------------------------------------------
# Initialisation — happy paths
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_model(self):
        svc = _make_service()
        assert svc.ai_model_id == MODELSLAB_DEFAULT_CHAT_MODEL

    def test_custom_model(self):
        svc = _make_service(ai_model_id="llama-3.1-70b-uncensored")
        assert svc.ai_model_id == "llama-3.1-70b-uncensored"

    def test_service_id_stored(self):
        svc = _make_service(service_id="my-modelslab")
        assert svc.service_id == "my-modelslab"

    def test_service_id_defaults_to_model_id(self):
        svc = _make_service()
        # SK behaviour: service_id defaults to ai_model_id when not supplied
        assert svc.service_id is not None

    def test_api_key_from_argument(self):
        """Passing api_key directly should not raise."""
        svc = ModelsLabChatCompletion(api_key="test-key-123")
        assert svc is not None

    def test_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("MODELSLAB_API_KEY", "env-key-xyz")
        svc = ModelsLabChatCompletion()
        assert svc is not None

    def test_custom_base_url(self):
        """Service initialises cleanly with a custom base URL."""
        svc = ModelsLabChatCompletion(
            api_key="k",
            base_url="https://custom.endpoint/v1",
        )
        assert svc is not None

    def test_base_url_from_env(self, monkeypatch):
        monkeypatch.setenv("MODELSLAB_CHAT_BASE_URL", "https://my-proxy/v1")
        svc = ModelsLabChatCompletion(api_key="k")
        assert svc is not None

    def test_model_from_env(self, monkeypatch):
        monkeypatch.setenv("MODELSLAB_CHAT_MODEL_ID", "llama-3.1-70b-uncensored")
        svc = _make_service()
        assert svc.ai_model_id == "llama-3.1-70b-uncensored"

    def test_async_client_bypasses_key_check(self):
        """When an async_client is supplied, no API key is required."""
        mock_client = MagicMock(spec=AsyncOpenAI)
        svc = ModelsLabChatCompletion(async_client=mock_client)
        assert svc is not None


# ---------------------------------------------------------------------------
# Initialisation — error paths
# ---------------------------------------------------------------------------

class TestInitErrors:
    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("MODELSLAB_API_KEY", raising=False)
        with pytest.raises(ServiceInitializationError, match="API key"):
            ModelsLabChatCompletion()

    def test_unknown_model_logs_warning(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            svc = ModelsLabChatCompletion(
                api_key="k",
                ai_model_id="gpt-4-not-real",
            )
        assert "not in the known" in caplog.text


# ---------------------------------------------------------------------------
# from_dict factory
# ---------------------------------------------------------------------------

class TestFromDict:
    def test_from_dict_creates_instance(self):
        svc = ModelsLabChatCompletion.from_dict({
            "ai_model_id": "llama-3.1-8b-uncensored",
            "service_id": "ml-svc",
            "api_key": "dict-key",
        })
        assert isinstance(svc, ModelsLabChatCompletion)
        assert svc.ai_model_id == "llama-3.1-8b-uncensored"

    def test_from_dict_empty_dict(self, monkeypatch):
        monkeypatch.setenv("MODELSLAB_API_KEY", "env-key")
        svc = ModelsLabChatCompletion.from_dict({})
        assert svc.ai_model_id == MODELSLAB_DEFAULT_CHAT_MODEL

    def test_from_dict_custom_base_url(self):
        svc = ModelsLabChatCompletion.from_dict({
            "api_key": "k",
            "base_url": "https://proxy.example.com/v1",
        })
        assert svc is not None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_default_model_in_model_list(self):
        assert MODELSLAB_DEFAULT_CHAT_MODEL in MODELSLAB_CHAT_MODELS

    def test_base_url_is_https(self):
        assert MODELSLAB_CHAT_BASE_URL.startswith("https://")

    def test_known_models(self):
        assert "llama-3.1-8b-uncensored" in MODELSLAB_CHAT_MODELS
        assert "llama-3.1-70b-uncensored" in MODELSLAB_CHAT_MODELS


# ---------------------------------------------------------------------------
# AsyncOpenAI client wiring
# ---------------------------------------------------------------------------

class TestClientWiring:
    def test_custom_client_is_used(self):
        """The supplied AsyncOpenAI client must be wired into the service."""
        mock_client = MagicMock(spec=AsyncOpenAI)
        svc = ModelsLabChatCompletion(async_client=mock_client)
        # OpenAIChatCompletion stores the client at .client
        assert svc.client is mock_client

    def test_default_client_points_to_modelslab(self):
        """When no client is given, the auto-built client must use ModelsLab URL."""
        with patch(
            "semantic_kernel.connectors.ai.modelslab.modelslab_chat_completion.AsyncOpenAI"
        ) as MockAsyncOpenAI:
            MockAsyncOpenAI.return_value = MagicMock(spec=AsyncOpenAI)
            svc = ModelsLabChatCompletion(api_key="test-key")

        call_kwargs = MockAsyncOpenAI.call_args.kwargs
        assert call_kwargs["base_url"] == MODELSLAB_CHAT_BASE_URL
        assert call_kwargs["api_key"] == "test-key"
