# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Iterable
from typing import Any, Union

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError

# TODO (eavanvalkenburg): replace back with google types once pydantic issue is fixed.
MessagesOptions = list[dict[str, Any]]

MessagePromptOption = Union[str, dict[str, Any]]
MessagePromptOptions = Union[MessagePromptOption, list[MessagePromptOption]]

ExampleOptions = Union[dict[str, Any], list[dict[str, Any]]]


class GooglePalmPromptExecutionSettings(PromptExecutionSettings):
    ai_model_id: str | None = Field(None, serialization_alias="model")
    temperature: float = Field(0.0, ge=0.0, le=1.0)
    top_p: float = 1.0
    top_k: int = 1
    candidate_count: int = Field(1, ge=1, le=8)
    safety_settings: dict[str, Any] | None = None
    prompt: MessagePromptOptions | None = None


class GooglePalmTextPromptExecutionSettings(GooglePalmPromptExecutionSettings):
    max_output_tokens: int = Field(256, gt=0)
    stop_sequences: str | Iterable[str] | None = None


class GooglePalmChatPromptExecutionSettings(GooglePalmPromptExecutionSettings):
    messages: MessagesOptions | None = None
    examples: ExampleOptions | None = None
    context: str | None = None
    token_selection_biases: dict[int, int] | None = None

    @model_validator(mode="after")
    def validate_input(self):
        """Validate input."""
        if self.prompt is not None and (self.messages or self.context or self.examples):
            raise ServiceInvalidExecutionSettingsError("Prompt cannot be used without messages, context or examples")
