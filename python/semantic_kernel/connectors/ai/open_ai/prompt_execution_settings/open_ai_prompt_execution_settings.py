import logging
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field, field_validator, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError

logger = logging.getLogger(__name__)


class OpenAIPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for (Azure) OpenAI services."""

    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    logit_bias: Dict[Union[str, int], float] = Field(default_factory=dict)
    max_tokens: int = Field(256, gt=0)
    number_of_responses: int = Field(1, ge=1, le=128, serialization_alias="n")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0)
    seed: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    top_p: float = Field(1.0, ge=0.0, le=1.0)
    user: Optional[str] = None


class OpenAITextPromptExecutionSettings(OpenAIPromptExecutionSettings):
    """Specific settings for the completions endpoint."""

    prompt: Optional[str] = None
    best_of: Optional[int] = Field(None, ge=1)
    echo: bool = False
    logprobs: Optional[int] = Field(None, ge=0, le=5)
    suffix: Optional[str] = None

    @model_validator(mode="after")
    def check_best_of_and_n(self) -> "OpenAITextPromptExecutionSettings":
        """Check that the best_of parameter is not greater than the number_of_responses parameter."""
        if self.best_of is not None and self.best_of < self.number_of_responses:
            raise ServiceInvalidExecutionSettingsError(
                "When used with number_of_responses, best_of controls the number of candidate completions and n specifies how many to return, therefore best_of must be greater than number_of_responses."  # noqa: E501
            )
        if self.extension_data.get("best_of") is not None and self.extension_data["best_of"] < self.extension_data.get(
            "number_of_responses"
        ):
            raise ServiceInvalidExecutionSettingsError(
                "When used with number_of_responses, best_of controls the number of candidate completions and n specifies how many to return, therefore best_of must be greater than number_of_responses."  # noqa: E501
            )
        return self


class OpenAIChatPromptExecutionSettings(OpenAIPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: Optional[Dict[Literal["type"], Literal["text", "json_object"]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    function_call: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    auto_invoke_kernel_functions: Optional[bool] = Field(default=False, exclude=True)
    max_auto_invoke_attempts: Optional[int] = Field(default=5, exclude=True)

    @field_validator("functions", "function_call", mode="after")
    @classmethod
    def validate_function_call(cls, v: Optional[Union[str, List[Dict[str, Any]]]] = None):
        if v is not None:
            logger.warning(
                "The function_call and functions parameters are deprecated. Please use the tool_choice and tools parameters instead."  # noqa: E501
            )
        return v


class OpenAIEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    input: Optional[Union[str, List[str], List[int], List[List[int]]]] = None
    ai_model_id: Optional[str] = Field(None, serialization_alias="model")
    encoding_format: Optional[Literal["float", "base64"]] = None
    user: Optional[str] = None
    extra_headers: Optional[Dict] = None
    extra_query: Optional[Dict] = None
    extra_body: Optional[Dict] = None
    timeout: Optional[float] = None
