# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Annotated, Any, Literal

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from pydantic import BaseModel, Field, field_validator, model_validator

from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError

logger = logging.getLogger(__name__)


class OpenAIPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for (Azure) OpenAI services."""

    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None
    frequency_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    logit_bias: dict[str | int, float] | None = None
    max_tokens: Annotated[int | None, Field(gt=0)] = None
    number_of_responses: Annotated[int | None, Field(ge=1, le=128, serialization_alias="n")] = None
    presence_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    seed: int | None = None
    stop: str | list[str] | None = None
    stream: bool = False
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    user: str | None = None
    store: bool | None = None
    metadata: dict[str, str] | None = None


class OpenAITextPromptExecutionSettings(OpenAIPromptExecutionSettings):
    """Specific settings for the completions endpoint."""

    prompt: Annotated[
        str | None, Field(description="Do not set this manually. It is set by the service based on the text content.")
    ] = None
    best_of: Annotated[int | None, Field(ge=1)] = None
    echo: bool = False
    logprobs: Annotated[int | None, Field(ge=0, le=5)] = None
    suffix: str | None = None

    @model_validator(mode="after")
    def check_best_of_and_n(self) -> "OpenAITextPromptExecutionSettings":
        """Check that the best_of parameter is not greater than the number_of_responses parameter."""
        best_of = self.best_of or self.extension_data.get("best_of")
        number_of_responses = self.number_of_responses or self.extension_data.get("number_of_responses")

        if best_of is not None and number_of_responses is not None and best_of < number_of_responses:
            raise ServiceInvalidExecutionSettingsError(
                "When used with number_of_responses, best_of controls the number of candidate completions and n specifies how many to return, therefore best_of must be greater than number_of_responses."  # noqa: E501
            )

        return self


class OpenAIChatPromptExecutionSettings(OpenAIPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: (
        dict[Literal["type"], Literal["text", "json_object"]] | dict[str, Any] | type[BaseModel] | type | None
    ) = None
    function_call: str | None = None
    functions: list[dict[str, Any]] | None = None
    messages: Annotated[
        list[dict[str, Any]] | None, Field(description="Do not set this manually. It is set by the service.")
    ] = None
    function_call_behavior: Annotated[FunctionCallBehavior | None, Field(exclude=True)] = None
    parallel_tool_calls: bool | None = True
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    tool_choice: Annotated[
        str | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    structured_json_response: Annotated[
        bool, Field(description="Do not set this manually. It is set by the service.")
    ] = False
    stream_options: Annotated[
        dict[str, Any] | None,
        Field(description="Additional options to pass when streaming is used. Do not set this manually."),
    ] = None
    max_completion_tokens: Annotated[
        int | None,
        Field(
            gt=0,
            description="A maximum limit on total tokens for completion, including both output and reasoning tokens.",
        ),
    ] = None
    reasoning_effort: Annotated[
        Literal["low", "medium", "high"] | None,
        Field(
            description="Adjusts reasoning effort (low/medium/high). Lower values reduce response time and token usage."
        ),
    ] = None

    @field_validator("functions", "function_call", mode="after")
    @classmethod
    def validate_function_call(cls, v: str | list[dict[str, Any]] | None = None):
        """Validate the function_call and functions parameters."""
        if v is not None:
            logger.warning(
                "The function_call and functions parameters are deprecated. Please use the tool_choice and tools parameters instead."  # noqa: E501
            )
        return v

    @model_validator(mode="before")
    def validate_response_format_and_set_flag(cls, values) -> Any:
        """Validate the response_format and set structured_json_response accordingly."""
        response_format = values.get("response_format", None)

        if response_format is None:
            return values

        if isinstance(response_format, dict):
            if response_format.get("type") == "json_object":
                return values
            if response_format.get("type") == "json_schema":
                json_schema = response_format.get("json_schema")
                if isinstance(json_schema, dict):
                    values["structured_json_response"] = True
                    return values
                raise ServiceInvalidExecutionSettingsError(
                    "If response_format has type 'json_schema', 'json_schema' must be a valid dictionary."
                )
        if isinstance(response_format, type):
            if issubclass(response_format, BaseModel):
                values["structured_json_response"] = True
            else:
                values["structured_json_response"] = True
        else:
            raise ServiceInvalidExecutionSettingsError(
                "response_format must be a dictionary, a subclass of BaseModel, a Python class/type, or None"
            )

        return values

    @model_validator(mode="before")
    @classmethod
    def validate_function_calling_behaviors(cls, data) -> Any:
        """Check if function_call_behavior is set and if so, move to use function_choice_behavior instead."""
        # In an attempt to phase out the use of `function_call_behavior` in favor of `function_choice_behavior`,
        # we are syncing the `function_call_behavior` with `function_choice_behavior` if the former is set.
        # This allows us to make decisions off of `function_choice_behavior`. Anytime the `function_call_behavior`
        # is updated, this validation will run to ensure the `function_choice_behavior` stays in sync.
        from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

        if isinstance(data, dict) and "function_call_behavior" in data.get("extension_data", {}):
            data["function_choice_behavior"] = FunctionChoiceBehavior.from_function_call_behavior(
                data.get("extension_data", {}).get("function_call_behavior")
            )
        return data

    @field_validator("function_call_behavior", mode="after")
    @classmethod
    def check_for_function_call_behavior(cls, v) -> Self:
        """Check if function_choice_behavior is set, if not, set it to default."""
        if v is not None:
            logger.warning(
                "The `function_call_behavior` parameter is deprecated. Please use the `function_choice_behavior` parameter instead."  # noqa: E501
            )
        return v


class OpenAIEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Specific settings for the text embedding endpoint."""

    input: str | list[str] | list[int] | list[list[int]] | None = None
    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None
    encoding_format: Literal["float", "base64"] | None = None
    user: str | None = None
    extra_headers: dict | None = None
    extra_query: dict | None = None
    extra_body: dict | None = None
    timeout: float | None = None
    dimensions: Annotated[int | None, Field(gt=0, le=3072)] = None
