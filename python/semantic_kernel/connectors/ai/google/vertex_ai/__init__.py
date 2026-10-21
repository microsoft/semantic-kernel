# Copyright (c) Microsoft. All rights reserved.

import warnings

from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_chat_completion import VertexAIChatCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_completion import VertexAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_embedding import VertexAITextEmbedding
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIChatPromptExecutionSettings,
    VertexAIEmbeddingPromptExecutionSettings,
    VertexAIPromptExecutionSettings,
    VertexAITextPromptExecutionSettings,
)

# Deprecation warning for the entire Vertex AI package
warnings.warn(
    "The `semantic_kernel.connectors.ai.google.vertex_ai` package is deprecated and will be removed after 01/01/2026. "
    "Please use `semantic_kernel.connectors.ai.google` instead for Google AI services.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "VertexAIChatCompletion",
    "VertexAIChatPromptExecutionSettings",
    "VertexAIEmbeddingPromptExecutionSettings",
    "VertexAIPromptExecutionSettings",
    "VertexAITextCompletion",
    "VertexAITextEmbedding",
    "VertexAITextPromptExecutionSettings",
]
