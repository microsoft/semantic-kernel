# Copyright (c) Microsoft. All rights reserved.


from typing import Any

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class BedrockPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Prompt Execution Settings."""

    temperature: float | None = Field(None, ge=0.0, le=1.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    top_k: int | None = Field(None, gt=0)
    max_tokens: int | None = Field(None, gt=0)
    stop: list[str] = Field(default_factory=list)


class BedrockChatPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Chat Prompt Execution Settings."""

    tools: list[dict[str, Any]] | None = Field(
        None,
        max_length=64,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )
    tool_choice: dict[str, Any] | None = Field(
        None,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )


class BedrockTextPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Text Prompt Execution Settings."""

    ...


class BedrockEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Embedding Prompt Execution Settings."""

    ...
