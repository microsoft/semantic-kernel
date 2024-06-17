# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)


class AzureAIInferencePromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Prompt Execution Settings."""

    frequency_penalty: float | None = Field(None, ge=-2, le=2)
    max_tokens: int | None = Field(None, gt=0)
    presence_penalty: float | None = Field(None, ge=-2, le=2)
    seed: int | None = None
    stop: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    # `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    extra_parameters: dict[str, str] | None = None


class AzureAIInferenceChatPromptExecutionSettings(
    AzureAIInferencePromptExecutionSettings
):
    """Azure AI Inference Chat Prompt Execution Settings."""


class AzureAIInferenceEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Embedding Prompt Execution Settings."""

    dimensions: int | None = Field(1024, gt=0)
    # Known values for `encoding_format` are
    # "base64", "binary", "float", "int8", "ubinary", and "uint8".
    encoding_format: str | None = None
    # Known values for `input_type` are "text", "query", and "document"
    input_type: str | None = None
    # `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    extra_parameters: dict[str, str] | None = None
