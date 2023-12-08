from typing import Any, Dict, Iterable, Optional, Union

from google.generativeai.types import (
    ExampleOptions,
    MessagePromptOptions,
    MessagesOptions,
)
from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class GooglePalmRequestSettings(AIRequestSettings):
    temperature: float = Field(0.0, ge=0.0, le=1.0)
    top_p: float = 1.0
    top_k: float = 1.0
    candidate_count: int = Field(1, ge=1, le=8)
    safety_settings: Optional[Dict[str, Any]] = None
    prompt: Optional[MessagePromptOptions] = None


class GooglePalmTextRequestSettings(GooglePalmRequestSettings):
    max_output_tokens: int = Field(256, gt=0)
    stop_sequences: Optional[Union[str, Iterable[str]]] = None


class GooglePalmChatRequestSettings(GooglePalmRequestSettings):
    messages: Optional[MessagesOptions] = None
    examples: Optional[ExampleOptions] = None
    context: Optional[str] = None
    token_selection_biases: Dict[int, int] = {}

    @model_validator(mode="after")
    def validate_input(self):
        if self.prompt is not None:
            if self.messages or self.context or self.examples:
                raise ValueError(
                    "Prompt cannot be used with messages, context or examples"
                )
