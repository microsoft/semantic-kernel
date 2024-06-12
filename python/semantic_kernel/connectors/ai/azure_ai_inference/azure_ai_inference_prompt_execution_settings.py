# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)


class AzureAIInferencePromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Prompt Execution Settings."""

    frequency_penalty: float = Field(0.0, ge=0.0, le=1.0)
    max_tokens: int = Field(256, gt=0)
    presence_penalty: float = Field(0.0, ge=0.0, le=1.0)
    seed: int | None = None
    stop: str | None = None
    temperature: float = Field(1.0, ge=0.0, le=1.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    # `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    extra_parameters: dict[str, str] | None = None


class AzureAIInferenceChatPromptExecutionSettings(
    AzureAIInferencePromptExecutionSettings
):
    """Azure AI Inference Chat Prompt Execution Settings."""


class AzureAIInferenceEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Embedding Prompt Execution Settings."""

    dimensions: int = Field(1024, gt=0)
    encoding_format: str = "json"
    input_type: str = "text"
