import logging
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_CHAT_SYSTEM_PROMPT

if TYPE_CHECKING:
    from semantic_kernel.semantic_functions.prompt_template_config import (
        PromptTemplateConfig,
    )

_LOGGER = logging.getLogger(__name__)


class OpenAIRequestSettings(AIRequestSettings):
    temperature: float = 0.0
    top_p: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    results_per_prompt: int = 1
    max_tokens: int = 256
    token_selection_biases: Dict[int, int] = Field(default_factory=dict)
    stop: List[str] = Field(default_factory=list)
    function_call: Optional[str] = None
    tool_choice: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    response_format: Literal["text", "json_object"] = "text"
    user_id: Optional[str] = None
    chat_system_prompt: Optional[str] = DEFAULT_CHAT_SYSTEM_PROMPT

    @field_validator("function_call")
    @classmethod
    def validate_function_call(cls, v: Any):
        if v is not None:
            _LOGGER.warning(
                "The function_call parameter is deprecated. Please use the tool_choice parameter instead."
            )

    def create_options(self, **kwargs) -> Dict[str, Any]:
        if "chat_mode" in kwargs and kwargs["chat_mode"]:
            return self.model_dump(exclude={"service_id", "extension_data"})
        return self.model_dump(
            exclude={"service_id", "extension_data", "chat_system_prompt"}
        )

    def update_from_completion_config(
        self, completion_config: "PromptTemplateConfig.CompletionConfig"
    ):
        self.temperature = completion_config.temperature
        self.top_p = completion_config.top_p
        self.number_of_responses = completion_config.number_of_responses
        self.stop_sequences = completion_config.stop_sequences
        self.max_tokens = completion_config.max_tokens
        self.presence_penalty = completion_config.presence_penalty
        self.frequency_penalty = completion_config.frequency_penalty
        self.token_selection_biases = completion_config.token_selection_biases
        self.function_call = (
            completion_config.function_call
            if hasattr(completion_config, "function_call")
            else None
        )

    @classmethod
    def from_completion_config(
        cls,
        completion_config: "PromptTemplateConfig.CompletionConfig",
    ) -> "OpenAIRequestSettings":
        settings = cls()
        settings.update_from_completion_config(completion_config)
        return settings
