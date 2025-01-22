# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import AnthropicChatCompletion
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import GoogleAIChatCompletion
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion import GoogleAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_chat_completion import VertexAIChatCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_completion import VertexAITextCompletion
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import OllamaTextCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion

pytestmark = pytest.mark.parametrize(
    "decorated_method, expected_attribute",
    [
        # OpenAIChatCompletion
        pytest.param(
            OpenAIChatCompletion._inner_get_chat_message_contents,
            "__model_diagnostics_chat_completion__",
            id="OpenAIChatCompletion._inner_get_chat_message_contents",
        ),
        pytest.param(
            OpenAIChatCompletion._inner_get_streaming_chat_message_contents,
            "__model_diagnostics_streaming_chat_completion__",
            id="OpenAIChatCompletion._inner_get_streaming_chat_message_contents",
        ),
        # OpenAITextCompletion
        pytest.param(
            OpenAITextCompletion._inner_get_text_contents,
            "__model_diagnostics_text_completion__",
            id="OpenAITextCompletion._inner_get_text_contents",
        ),
        pytest.param(
            OpenAITextCompletion._inner_get_streaming_text_contents,
            "__model_diagnostics_streaming_text_completion__",
            id="OpenAITextCompletion._inner_get_streaming_text_contents",
        ),
        # OllamaChatCompletion
        pytest.param(
            OllamaChatCompletion._inner_get_chat_message_contents,
            "__model_diagnostics_chat_completion__",
            id="OllamaChatCompletion._inner_get_chat_message_contents",
        ),
        pytest.param(
            OllamaChatCompletion._inner_get_streaming_chat_message_contents,
            "__model_diagnostics_streaming_chat_completion__",
            id="OllamaChatCompletion._inner_get_streaming_chat_message_contents",
        ),
        # OllamaTextCompletion
        pytest.param(
            OllamaTextCompletion._inner_get_text_contents,
            "__model_diagnostics_text_completion__",
            id="OllamaTextCompletion._inner_get_text_contents",
        ),
        pytest.param(
            OllamaTextCompletion._inner_get_streaming_text_contents,
            "__model_diagnostics_streaming_text_completion__",
            id="OllamaTextCompletion._inner_get_streaming_text_contents",
        ),
        # MistralAIChatCompletion
        pytest.param(
            MistralAIChatCompletion._inner_get_chat_message_contents,
            "__model_diagnostics_chat_completion__",
            id="MistralAIChatCompletion._inner_get_chat_message_contents",
        ),
        pytest.param(
            MistralAIChatCompletion._inner_get_streaming_chat_message_contents,
            "__model_diagnostics_streaming_chat_completion__",
            id="MistralAIChatCompletion._inner_get_streaming_chat_message_contents",
        ),
        # VertexAIChatCompletion
        pytest.param(
            VertexAIChatCompletion._inner_get_chat_message_contents,
            "__model_diagnostics_chat_completion__",
            id="VertexAIChatCompletion._inner_get_chat_message_contents",
        ),
        pytest.param(
            VertexAIChatCompletion._inner_get_streaming_chat_message_contents,
            "__model_diagnostics_streaming_chat_completion__",
            id="VertexAIChatCompletion._inner_get_streaming_chat_message_contents",
        ),
        # VertexAITextCompletion
        pytest.param(
            VertexAITextCompletion._inner_get_text_contents,
            "__model_diagnostics_text_completion__",
            id="VertexAITextCompletion._inner_get_text_contents",
        ),
        pytest.param(
            VertexAITextCompletion._inner_get_streaming_text_contents,
            "__model_diagnostics_streaming_text_completion__",
            id="VertexAITextCompletion._inner_get_streaming_text_contents",
        ),
        # GoogleAIChatCompletion
        pytest.param(
            GoogleAIChatCompletion._inner_get_chat_message_contents,
            "__model_diagnostics_chat_completion__",
            id="GoogleAIChatCompletion._inner_get_chat_message_contents",
        ),
        pytest.param(
            GoogleAIChatCompletion._inner_get_streaming_chat_message_contents,
            "__model_diagnostics_streaming_chat_completion__",
            id="GoogleAIChatCompletion._inner_get_streaming_chat_message_contents",
        ),
        # GoogleAITextCompletion
        pytest.param(
            GoogleAITextCompletion._inner_get_text_contents,
            "__model_diagnostics_text_completion__",
            id="GoogleAITextCompletion._inner_get_text_contents",
        ),
        pytest.param(
            GoogleAITextCompletion._inner_get_streaming_text_contents,
            "__model_diagnostics_streaming_text_completion__",
            id="GoogleAITextCompletion._inner_get_streaming_text_contents",
        ),
        # AnthropicChatCompletion
        pytest.param(
            AnthropicChatCompletion._inner_get_chat_message_contents,
            "__model_diagnostics_chat_completion__",
            id="AnthropicChatCompletion._inner_get_chat_message_contents",
        ),
        pytest.param(
            AnthropicChatCompletion._inner_get_streaming_chat_message_contents,
            "__model_diagnostics_streaming_chat_completion__",
            id="AnthropicChatCompletion._inner_get_streaming_chat_message_contents",
        ),
    ],
)


def test_decorated(decorated_method, expected_attribute):
    """Test that the connectors are being decorated properly with the model diagnostics decorators."""
    assert hasattr(decorated_method, expected_attribute) and getattr(decorated_method, expected_attribute), (
        f"{decorated_method} should be decorated with the appropriate model diagnostics decorator."
    )
