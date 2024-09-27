# Copyright (c) Microsoft. All rights reserved.


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

    ...


class BedrockTextPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Text Prompt Execution Settings."""

    ...


class BedrockEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Embedding Prompt Execution Settings."""

    ...
