# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
    GoogleAIEmbeddingPromptExecutionSettings,
    GoogleAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import GoogleAIChatCompletion
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion import GoogleAITextCompletion
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_embedding import GoogleAITextEmbedding
from semantic_kernel.const import USER_AGENT
from semantic_kernel.contents.chat_history import ChatHistory


async def test_google_ai_chat_completion_user_agent(google_ai_unit_test_env):
    """Test that GoogleAIChatCompletion sends the User-Agent header."""
    chat_history = ChatHistory()
    chat_history.add_user_message("hi")

    with patch(
        "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion.Client"
    ) as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAIChatCompletion(gemini_model_id="gemini-3-flash-preview", api_key="test-api-key")

        await service.get_chat_message_contents(
            chat_history=chat_history, settings=GoogleAIChatPromptExecutionSettings()
        )

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is not None
        assert "headers" in kwargs["http_options"]
        assert USER_AGENT in kwargs["http_options"]["headers"]
        assert "semantic-kernel-python" in kwargs["http_options"]["headers"][USER_AGENT]


async def test_google_ai_chat_completion_vertex_ai_user_agent(google_ai_unit_test_env):
    """Test that GoogleAIChatCompletion sends the User-Agent header with Vertex AI."""
    chat_history = ChatHistory()
    chat_history.add_user_message("hi")

    with patch(
        "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion.Client"
    ) as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAIChatCompletion(
            gemini_model_id="gemini-3-flash-preview",
            use_vertexai=True,
            project_id="test-project",
            region="test-region",
        )

        await service.get_chat_message_contents(
            chat_history=chat_history, settings=GoogleAIChatPromptExecutionSettings()
        )

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is not None
        assert "headers" in kwargs["http_options"]
        assert USER_AGENT in kwargs["http_options"]["headers"]
        assert "semantic-kernel-python" in kwargs["http_options"]["headers"][USER_AGENT]


async def test_google_ai_chat_completion_no_telemetry(google_ai_unit_test_env):
    """Test that GoogleAIChatCompletion does not send the User-Agent header when telemetry is disabled."""
    chat_history = ChatHistory()
    chat_history.add_user_message("hi")

    with (
        patch("semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base.IS_TELEMETRY_ENABLED", False),
        patch(
            "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion.Client"
        ) as mock_client,
    ):
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAIChatCompletion(gemini_model_id="gemini-3-flash-preview", api_key="test-api-key")

        await service.get_chat_message_contents(
            chat_history=chat_history, settings=GoogleAIChatPromptExecutionSettings()
        )

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is None


async def test_google_ai_text_completion_user_agent(google_ai_unit_test_env):
    """Test that GoogleAITextCompletion sends the User-Agent header."""
    with patch(
        "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion.Client"
    ) as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAITextCompletion(gemini_model_id="gemini-3-flash-preview", api_key="test-api-key")

        await service.get_text_contents(prompt="hi", settings=GoogleAITextPromptExecutionSettings())

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is not None
        assert "headers" in kwargs["http_options"]
        assert USER_AGENT in kwargs["http_options"]["headers"]
        assert "semantic-kernel-python" in kwargs["http_options"]["headers"][USER_AGENT]


async def test_google_ai_text_completion_no_telemetry(google_ai_unit_test_env):
    """Test that GoogleAITextCompletion does not send the User-Agent header when telemetry is disabled."""
    with (
        patch("semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base.IS_TELEMETRY_ENABLED", False),
        patch(
            "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion.Client"
        ) as mock_client,
    ):
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAITextCompletion(gemini_model_id="gemini-3-flash-preview", api_key="test-api-key")

        await service.get_text_contents(prompt="hi", settings=GoogleAITextPromptExecutionSettings())

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is None


async def test_google_ai_text_embedding_user_agent(google_ai_unit_test_env):
    """Test that GoogleAITextEmbedding sends the User-Agent header."""
    with patch(
        "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_embedding.Client"
    ) as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.embed_content = AsyncMock()

        service = GoogleAITextEmbedding(embedding_model_id="gemini-embedding-2-preview", api_key="test-api-key")

        await service.generate_embeddings(texts=["hi"], settings=GoogleAIEmbeddingPromptExecutionSettings())

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is not None
        assert "headers" in kwargs["http_options"]
        assert USER_AGENT in kwargs["http_options"]["headers"]
        assert "semantic-kernel-python" in kwargs["http_options"]["headers"][USER_AGENT]


async def test_google_ai_text_embedding_no_telemetry(google_ai_unit_test_env):
    """Test that GoogleAITextEmbedding does not send the User-Agent header when telemetry is disabled."""
    with (
        patch("semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base.IS_TELEMETRY_ENABLED", False),
        patch(
            "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_embedding.Client"
        ) as mock_client,
    ):
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.embed_content = AsyncMock()

        service = GoogleAITextEmbedding(embedding_model_id="gemini-embedding-2-preview", api_key="test-api-key")

        await service.generate_embeddings(texts=["hi"], settings=GoogleAIEmbeddingPromptExecutionSettings())

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is None
