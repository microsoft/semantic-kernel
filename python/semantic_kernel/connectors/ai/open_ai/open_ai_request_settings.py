import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_CHAT_SYSTEM_PROMPT

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class OpenAIRequestSettings(AIRequestSettings):
    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    best_of: Optional[int] = Field(None, ge=1)
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    logit_bias: Dict[str, float] = Field(default_factory=dict)
    logprobs: Optional[int] = Field(None, ge=0, le=5)
    max_tokens: int = Field(256, gt=0)
    number_of_responses: int = Field(1, ge=1, serialization_alias="n")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    response_format: Literal["text", "json_object"] = "text"
    seed: Optional[int] = None
    stop: Optional[List[str]] = Field(default=None, max_length=4)
    stream: bool = False
    suffix: Optional[str] = None
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    user: Optional[str] = None
    function_call: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = [
        {"role": "system", "content": DEFAULT_CHAT_SYSTEM_PROMPT}
    ]
    prompt: Optional[str] = None

    @field_validator("function_call", "functions")
    @classmethod
    def validate_function_call(cls, v: Any):
        if v is not None:
            _LOGGER.warning(
                "The function_call and functions parameters are deprecated. Please use the tool_choice and tools parameters instead."
            )

    def create_options(self, **kwargs) -> Dict[str, Any]:
        """Creates the options for the request."""
        if kwargs.get("chat_mode", False):  # chat completion
            settings = self.model_dump(
                exclude={
                    "service_id",
                    "extension_data",
                    "prompt",
                    "logprobs",
                    "suffix",
                },
                exclude_unset=True,
                exclude_none=True,
                by_alias=True,
            )
            if self.function_call is None and "functions" in settings:
                del settings["functions"]
            if self.tool_choice is None and "tools" in settings:
                del settings["tools"]
        else:  # text completion
            settings = self.model_dump(
                exclude={
                    "service_id",
                    "extension_data",
                    "messages",
                    "function_call",
                    "functions",
                    "tool_choice",
                    "tools",
                },
                exclude_unset=True,
                exclude_none=True,
                by_alias=True,
            )
            if self.best_of:
                if self.best_of > self.number_of_responses:
                    settings["best_of"] = self.number_of_responses
                    _LOGGER.warning(
                        "The best_of parameter must be greater than or equal to the number_of_responses parameter. The best_of parameter has been set to %s.",
                        self.number_of_responses,
                    )
        return settings

    # def update_from_completion_config(
    #     self, completion_config: "PromptConfig.CompletionConfig"
    # ):
    #     self.temperature = completion_config.temperature
    #     self.top_p = completion_config.top_p
    #     self.number_of_responses = completion_config.number_of_responses
    #     self.stop_sequences = completion_config.stop_sequences
    #     self.max_tokens = completion_config.max_tokens
    #     self.presence_penalty = completion_config.presence_penalty
    #     self.frequency_penalty = completion_config.frequency_penalty
    #     self.token_selection_biases = completion_config.token_selection_biases
    #     self.function_call = (
    #         completion_config.function_call
    #         if hasattr(completion_config, "function_call")
    #         else None
    #     )

    def update_from_openai_request_settings(
        self, new_settings: "OpenAIRequestSettings"
    ) -> None:
        """Update the request settings from another request settings."""
        for key, value in new_settings.model_dump().items():
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

    def update_from_extention_data(self, extension_data: Dict[str, Any]) -> None:
        """Update the request settings from extension data."""
        for key, value in extension_data.items():
            if key in self.keys:
                setattr(self, key, value)
