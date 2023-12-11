import logging
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, field_validator, model_validator

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_CHAT_SYSTEM_PROMPT

_LOGGER = logging.getLogger(__name__)


class OpenAIRequestSettings(AIRequestSettings):
    """Common request settings for (Azure) OpenAI services."""

    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    logit_bias: Dict[str, float] = Field(default_factory=dict)
    max_tokens: int = Field(256, gt=0)
    number_of_responses: int = Field(1, ge=1, serialization_alias="n")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    user: Optional[str] = None

    @field_validator("stop")
    @classmethod
    def validate_stop(cls, v: Any):
        if not v or isinstance(v, list):
            return v
        return [v]

    def update_from_openai_request_settings(
        self, new_settings: "OpenAIRequestSettings"
    ) -> None:
        """Update the request settings from another request settings."""
        for key, value in new_settings.model_dump().items():
            if key in self.keys:
                setattr(self, key, value)

    def update_from_extention_data(self, extension_data: Dict[str, Any]) -> None:
        """Update the request settings from extension data."""
        for key, value in extension_data.items():
            if key in self.keys:
                setattr(self, key, value)

    def update_from_ai_request_settings(
        self, ai_request_settings: AIRequestSettings
    ) -> None:
        """Update the request settings from another request settings."""
        self.service_id = ai_request_settings.service_id
        self.extension_data = ai_request_settings.extension_data
        self.update_from_extention_data(self.extension_data)

    @classmethod
    def from_ai_request(cls, ai_request: AIRequestSettings) -> "OpenAIRequestSettings":
        """Create OpenAI Request Settings from a generic AI Request Setting."""
        if isinstance(ai_request, cls):
            return ai_request
        return cls(
            service_id=ai_request.service_id, extension_data=ai_request.extension_data
        )


class OpenAITextRequestSettings(OpenAIRequestSettings):
    """Specific settings for the completions endpoint."""

    prompt: Optional[str] = None
    best_of: Optional[int] = Field(None, ge=1)
    echo: bool = False
    logprobs: Optional[int] = Field(None, ge=0, le=5)
    suffix: Optional[str] = None

    @model_validator(mode="after")
    def check_best_of_and_n(self) -> "OpenAITextRequestSettings":
        """Check that the best_of parameter is not greater than the number_of_responses parameter."""
        if self.best_of and self.best_of < self.number_of_responses:
            raise ValueError(
                "When used with number_of_responses, best_of controls the number of candidate completions and n specifies how many to return, therefore best_of must be greater than number_of_responses."  # noqa: E501
            )
        return self


class OpenAIChatRequestSettings(OpenAIRequestSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: Optional[Literal["text", "json_object"]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    function_call: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = [
        {"role": "system", "content": DEFAULT_CHAT_SYSTEM_PROMPT}
    ]

    @field_validator("function_call", "functions")
    @classmethod
    def validate_function_call(cls, v: Any):
        if v is not None:
            _LOGGER.warning(
                "The function_call and functions parameters are deprecated. Please use the tool_choice and tools parameters instead."  # noqa: E501
            )
