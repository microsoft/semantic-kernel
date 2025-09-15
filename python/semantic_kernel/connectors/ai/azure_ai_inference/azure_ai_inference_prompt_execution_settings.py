# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureAIInferencePromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Prompt Execution Settings.

    Note:
        `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    """

    frequency_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    max_tokens: Annotated[int | None, Field(gt=0)] = None
    presence_penalty: Annotated[float | None, Field(ge=-2.0, le=2.0)] = None
    seed: int | None = None
    stop: str | None = None
    temperature: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    extra_parameters: dict[str, Any] | None = None


@experimental
class AzureAIInferenceChatPromptExecutionSettings(AzureAIInferencePromptExecutionSettings):
    """Azure AI Inference Chat Prompt Execution Settings."""

    response_format: (
        dict[Literal["type"], Literal["text", "json_object"]] | dict[str, Any] | type[BaseModel] | type | None
    ) = None
    structured_json_response: Annotated[
        bool, Field(description="Do not set this manually. It is set by the service.")
    ] = False
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

    @model_validator(mode="before")
    def validate_response_format_and_set_flag(cls, values: Any) -> Any:
        """Validate the response_format and set structured_json_response accordingly."""
        if not isinstance(values, dict):
            return values
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


@experimental
class AzureAIInferenceEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Azure AI Inference Embedding Prompt Execution Settings.

    Note:
        `extra_parameters` is a dictionary to pass additional model-specific parameters to the model.
    """

    dimensions: Annotated[int | None, Field(gt=0)] = None
    encoding_format: Literal["base64", "binary", "float", "int8", "ubinary", "uint8"] | None = None
    input_type: Literal["text", "query", "document"] | None = None
    extra_parameters: dict[str, str] | None = None
