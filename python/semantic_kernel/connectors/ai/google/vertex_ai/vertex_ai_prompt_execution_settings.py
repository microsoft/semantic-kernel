# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any, Literal

from pydantic import Field
from vertexai.generative_models import Tool, ToolConfig

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class VertexAIPromptExecutionSettings(PromptExecutionSettings):
    """Vertex AI Prompt Execution Settings."""

    stop_sequences: list[str] | None = Field(None, max_length=5)
    response_mime_type: Literal["text/plain", "application/json"] | None = None
    response_schema: Any | None = None
    candidate_count: int | None = Field(None, ge=1)
    max_output_tokens: int | None = Field(None, ge=1)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    top_p: float | None = None
    top_k: int | None = None


class VertexAITextPromptExecutionSettings(VertexAIPromptExecutionSettings):
    """Vertex AI Text Prompt Execution Settings."""

    pass


class VertexAIChatPromptExecutionSettings(VertexAIPromptExecutionSettings):
    """Vertex AI Chat Prompt Execution Settings."""

    tools: list[Tool] | None = Field(
        None,
        max_length=64,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )
    tool_config: ToolConfig | None = Field(
        None,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )

    @override
    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings as a dictionary for sending to the AI service.

        This method removes the tools and tool_config keys from the settings dictionary, as
        the Vertex AI service mandates these two settings to be sent as separate parameters.
        """
        settings_dict = super().prepare_settings_dict(**kwargs)
        settings_dict.pop("tools", None)
        settings_dict.pop("tool_config", None)

        return settings_dict


class VertexAIEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Google AI Embedding Prompt Execution Settings."""

    auto_truncate: bool | None = None
    output_dimensionality: int | None = None
