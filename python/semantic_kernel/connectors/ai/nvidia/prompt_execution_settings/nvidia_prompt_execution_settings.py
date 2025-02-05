# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, Any, Literal

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class NvidiaPromptExecutionSettings(PromptExecutionSettings):
    """Settings for NVIDIA prompt execution."""

    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None

    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings as a dictionary for sending to the AI service.

        By default, this method excludes the service_id and extension_data fields.
        As well as any fields that are None.
        """
        return self.model_dump(
            exclude={"service_id", "extension_data", "structured_json_response", "input_type"},
            exclude_none=True,
            by_alias=True,
        )


class NVIDIAEmbeddingPromptExecutionSettings(NvidiaPromptExecutionSettings):
    """Settings for NVIDIA embedding prompt execution."""

    """Specific settings for the text embedding endpoint."""

    input: str | list[str] | list[int] | list[list[int]] | None = None
    model: str = None
    encoding_format: Literal["float", "base64"] | None = "float"  # default to float
    truncate: Literal[None, "START", "END"] | None = None
    input_type: Literal["passage", "query"] | None = "passage"  # default to passage
    user: str | None = None
    extra_headers: dict | None = None
    extra_body: dict | None = None
    timeout: float | None = None
    dimensions: Annotated[int | None, Field(gt=0, le=3072)] = None
