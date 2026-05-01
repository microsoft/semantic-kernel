# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncOpenAI
from openai.resources.chat.completions import AsyncCompletions
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from semantic_kernel import __version__ as semantic_kernel_version
from semantic_kernel.connectors.ai.perplexity import (
    PerplexityChatCompletion,
    PerplexityChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.perplexity.services.perplexity_chat_completion import (
    PERPLEXITY_ATTRIBUTION_HEADER,
    PERPLEXITY_ATTRIBUTION_SLUG,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException


def _create_mock_chat_completion(content: str = "Hello!") -> ChatCompletion:
    message = ChatCompletionMessage(role="assistant", content=content)
    choice = Choice(finish_reason="stop", index=0, message=message)
    usage = CompletionUsage(completion_tokens=20, prompt_tokens=10, total_tokens=30)
    return ChatCompletion(
        id="test-id",
        choices=[choice],
        created=1234567890,
        model="sonar-pro",
        object="chat.completion",
        usage=usage,
    )


class TestPerplexityChatCompletion:
    """Test cases for PerplexityChatCompletion."""

    def test_init_with_defaults(self, perplexity_unit_test_env):
        """Service uses the env-supplied API key and default model."""
        service = PerplexityChatCompletion()
        assert service.ai_model_id == perplexity_unit_test_env["PERPLEXITY_CHAT_MODEL_ID"]
        assert str(service.client.base_url).rstrip("/") == "https://api.perplexity.ai"

    def test_default_model_is_sonar_pro(self, monkeypatch):
        """When no model env var is set, the connector defaults to 'sonar-pro'."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "k")
        monkeypatch.delenv("PERPLEXITY_CHAT_MODEL_ID", raising=False)
        service = PerplexityChatCompletion()
        assert service.ai_model_id == "sonar-pro"

    def test_init_with_custom_model(self, perplexity_unit_test_env):
        service = PerplexityChatCompletion(ai_model_id="sonar-pro")
        assert service.ai_model_id == "sonar-pro"

    def test_init_with_custom_base_url(self, perplexity_unit_test_env):
        service = PerplexityChatCompletion(base_url="https://example.test/api")
        assert str(service.client.base_url).rstrip("/") == "https://example.test/api"

    @pytest.mark.parametrize("exclude_list", [["PERPLEXITY_API_KEY"]], indirect=True)
    def test_init_with_missing_api_key(self, perplexity_unit_test_env):
        """A missing API key (and no provided client) raises a clear error."""
        with pytest.raises(ServiceInitializationError):
            PerplexityChatCompletion()

    def test_init_with_existing_client(self, perplexity_unit_test_env):
        """Passing an existing AsyncOpenAI client bypasses settings validation of api_key."""
        client = AsyncOpenAI(api_key="ignored", base_url="https://api.perplexity.ai")
        service = PerplexityChatCompletion(async_client=client)
        assert service.client is client

    def test_attribution_header_present_on_default_client(self, perplexity_unit_test_env):
        """Every outgoing request must carry the X-Pplx-Integration header."""
        service = PerplexityChatCompletion()
        headers = service.client.default_headers
        assert PERPLEXITY_ATTRIBUTION_HEADER in headers
        expected = f"{PERPLEXITY_ATTRIBUTION_SLUG}/{semantic_kernel_version}"
        assert headers[PERPLEXITY_ATTRIBUTION_HEADER] == expected

    def test_user_supplied_default_headers_are_merged(self, perplexity_unit_test_env):
        """Caller-provided headers are kept alongside the attribution header."""
        service = PerplexityChatCompletion(default_headers={"X-Custom": "yes"})
        headers = service.client.default_headers
        assert headers["X-Custom"] == "yes"
        assert PERPLEXITY_ATTRIBUTION_HEADER in headers

    def test_get_prompt_execution_settings_class(self, perplexity_unit_test_env):
        service = PerplexityChatCompletion()
        assert service.get_prompt_execution_settings_class() == PerplexityChatPromptExecutionSettings

    def test_service_url(self, perplexity_unit_test_env):
        service = PerplexityChatCompletion()
        assert "perplexity.ai" in service.service_url()

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_get_chat_message_contents(self, mock_create, perplexity_unit_test_env):
        mock_create.return_value = _create_mock_chat_completion("Hello!")

        service = PerplexityChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello")
        settings = PerplexityChatPromptExecutionSettings()

        result = await service.get_chat_message_contents(chat_history, settings)

        assert len(result) == 1
        assert result[0].content == "Hello!"
        # The model parameter should default to the configured one (sonar-pro).
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs.get("model") == "sonar-pro"

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_search_filters_passed_through(self, mock_create, perplexity_unit_test_env):
        """Perplexity-specific filter fields are forwarded on the request."""
        mock_create.return_value = _create_mock_chat_completion("ok")

        service = PerplexityChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("news")
        settings = PerplexityChatPromptExecutionSettings(
            search_recency_filter="day",
            search_domain_filter=["wikipedia.org"],
        )

        await service.get_chat_message_contents(chat_history, settings)

        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["search_recency_filter"] == "day"
        assert call_kwargs["search_domain_filter"] == ["wikipedia.org"]

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_error_handling(self, mock_create, perplexity_unit_test_env):
        mock_create.side_effect = Exception("API Error")

        service = PerplexityChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello")

        with pytest.raises(ServiceResponseException):
            await service.get_chat_message_contents(chat_history, PerplexityChatPromptExecutionSettings())
