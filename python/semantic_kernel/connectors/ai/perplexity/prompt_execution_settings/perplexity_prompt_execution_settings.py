# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class PerplexityPromptExecutionSettings(PromptExecutionSettings):
    """Common settings for Perplexity prompt execution."""

    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None


class PerplexityChatPromptExecutionSettings(PerplexityPromptExecutionSettings):
    """Settings for Perplexity chat prompt execution.

    Mirrors the OpenAI chat parameter shape (the Perplexity Agent API is OpenAI-compatible),
    plus a small set of Perplexity-specific search controls that are passed through as
    top-level fields on the request body.
    """

    messages: list[dict[str, Any]] | None = None
    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    top_k: Annotated[int | None, Field(ge=0)] = None
    n: Annotated[int | None, Field(ge=1)] = None
    stream: bool = False
    stop: str | list[str] | None = None
    max_tokens: Annotated[int | None, Field(ge=1)] = None
    presence_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    frequency_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    response_format: (
        dict[Literal["type"], Literal["text", "json_object"]] | dict[str, Any] | type[BaseModel] | type | None
    ) = None
    user: str | None = None
    extra_headers: dict | None = None
    extra_body: dict | None = None
    timeout: float | None = None
    # Perplexity-specific search parameters
    search_domain_filter: list[str] | None = None
    search_recency_filter: Literal["hour", "day", "week", "month", "year"] | None = None
    return_images: bool | None = None
    return_related_questions: bool | None = None
