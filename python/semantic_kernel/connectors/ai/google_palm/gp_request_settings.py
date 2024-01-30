from typing import Any, Dict, Iterable, List, Optional, Union

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings

# TODO: replace back with google types once pydantic issue is fixed.
MessagesOptions = List[Dict[str, Any]]

MessagePromptOption = Union[str, Dict[str, Any]]
MessagePromptOptions = Union[MessagePromptOption, List[MessagePromptOption]]

ExampleOptions = Union[Dict[str, Any], List[Dict[str, Any]]]


class GooglePalmRequestSettings(AIRequestSettings):
    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    temperature: float = Field(0.0, ge=0.0, le=1.0)
    top_p: float = 1.0
    top_k: int = 1
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
    token_selection_biases: Optional[Dict[int, int]] = None

    @model_validator(mode="after")
    def validate_input(self):
        if self.prompt is not None:
            if self.messages or self.context or self.examples:
                raise ValueError("Prompt cannot be used with messages, context or examples")
