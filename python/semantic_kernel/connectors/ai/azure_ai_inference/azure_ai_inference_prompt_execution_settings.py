# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Literal

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureAIInferencePromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Prompt Execution Settings.

    Note:
        `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    """

    frequency_penalty: float | None = Field(None, ge=-2, le=2)
    max_tokens: int | None = Field(None, gt=0)
    presence_penalty: float | None = Field(None, ge=-2, le=2)
    seed: int | None = None
    stop: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=1.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    extra_parameters: dict[str, Any] | None = None


@experimental_class
class AzureAIInferenceChatPromptExecutionSettings(AzureAIInferencePromptExecutionSettings):
    """Azure AI Inference Chat Prompt Execution Settings."""

    tools: list[dict[str, Any]] | None = Field(
        None,
        max_length=64,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )
    tool_choice: str | None = Field(
        None,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )


@experimental_class
class AzureAIInferenceEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Embedding Prompt Execution Settings.

    Note:
        `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    """

    dimensions: int | None = Field(None, gt=0)
    encoding_format: Literal["base64", "binary", "float", "int8", "ubinary", "uint8"] | None = None
    input_type: Literal["text", "query", "document"] | None = None
    extra_parameters: dict[str, str] | None = None
