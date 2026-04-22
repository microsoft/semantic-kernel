# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class AstraflowPromptExecutionSettings(PromptExecutionSettings):
    """Base settings for Astraflow prompt execution."""


class AstraflowEmbeddingPromptExecutionSettings(AstraflowPromptExecutionSettings):
    """Settings for Astraflow embedding prompt execution."""

    input: str | list[str] | None = None
    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None
    encoding_format: Literal["float", "base64"] = "float"
    user: str | None = None
    extra_headers: dict | None = None
    extra_body: dict | None = None
    timeout: float | None = None
    dimensions: Annotated[int | None, Field(gt=0)] = None

    def prepare_settings_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Return a dict of settings ready to pass to the OpenAI embeddings endpoint."""
        return self.model_dump(
            exclude={"service_id", "extension_data", "structured_json_response"},
            exclude_none=True,
            by_alias=True,
        )


class AstraflowChatPromptExecutionSettings(AstraflowPromptExecutionSettings):
    """Settings for Astraflow chat prompt execution."""

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

    def prepare_settings_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Return a dict of settings ready to pass to the OpenAI chat completions endpoint."""
        return self.model_dump(
            exclude={"service_id", "extension_data", "structured_json_response", "response_format"},
            exclude_none=True,
            by_alias=True,
        )
