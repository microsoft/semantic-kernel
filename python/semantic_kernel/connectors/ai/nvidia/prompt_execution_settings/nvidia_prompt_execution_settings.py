# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class NvidiaPromptExecutionSettings(PromptExecutionSettings):
    """Settings for NVIDIA prompt execution."""

    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None


class NvidiaEmbeddingPromptExecutionSettings(NvidiaPromptExecutionSettings):
    """Settings for NVIDIA embedding prompt execution."""

    input: str | list[str] | None = None
    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None
    encoding_format: Literal["float", "base64"] = "float"
    truncate: Literal["NONE", "START", "END"] = "NONE"
    input_type: Literal["passage", "query"] = "query"  # required param with default value query
    user: str | None = None
    extra_headers: dict | None = None
    extra_body: dict | None = None
    timeout: float | None = None
    dimensions: Annotated[int | None, Field(gt=0)] = None

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Override only for embeddings to exclude input_type and truncate."""
        return self.model_dump(
            exclude={"service_id", "extension_data", "structured_json_response", "input_type", "truncate"},
            exclude_none=True,
            by_alias=True,
        )


class NvidiaChatPromptExecutionSettings(NvidiaPromptExecutionSettings):
    """Settings for NVIDIA chat prompt execution."""

    messages: list[dict[str, str]] | None = None
    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None
    temperature: float | None = None
    top_p: float | None = None
    n: int | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    max_tokens: int | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: (
        dict[Literal["type"], Literal["text", "json_object"]] | dict[str, Any] | type[BaseModel] | type | None
    ) = None
    seed: int | None = None
    extra_headers: dict | None = None
    extra_body: dict | None = None
    timeout: float | None = None
    # NVIDIA-specific structured output support
    nvext: dict[str, Any] | None = None

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Override only for embeddings to exclude input_type and truncate."""
        return self.model_dump(
            exclude={"service_id", "extension_data", "structured_json_response", "response_format"},
            exclude_none=True,
            by_alias=True,
        )
