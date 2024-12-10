# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Annotated, Any, Literal

from pydantic import Field

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class GoogleAIPromptExecutionSettings(PromptExecutionSettings):
    """Google AI Prompt Execution Settings."""

    stop_sequences: Annotated[list[str] | None, Field(max_length=5)] = None
    response_mime_type: Literal["text/plain", "application/json"] | None = None
    response_schema: Any | None = None
    candidate_count: Annotated[int | None, Field(ge=1)] = None
    max_output_tokens: Annotated[int | None, Field(ge=1)] = None
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    top_p: float | None = None
    top_k: int | None = None


class GoogleAITextPromptExecutionSettings(GoogleAIPromptExecutionSettings):
    """Google AI Text Prompt Execution Settings."""

    pass


class GoogleAIChatPromptExecutionSettings(GoogleAIPromptExecutionSettings):
    """Google AI Chat Prompt Execution Settings."""

    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    tool_config: Annotated[
        dict[str, Any] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None

    @override
    def prepare_settings_dict(self, **kwargs) -> dict[str, Any]:
        """Prepare the settings as a dictionary for sending to the AI service.

        This method removes the tools and tool_choice keys from the settings dictionary, as
        the Google AI service mandates these two settings to be sent as separate parameters.
        """
        settings_dict = super().prepare_settings_dict(**kwargs)
        settings_dict.pop("tools", None)
        settings_dict.pop("tool_config", None)

        return settings_dict


class GoogleAIEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Google AI Embedding Prompt Execution Settings."""

    output_dimensionality: Annotated[int | None, Field(le=768)] = None
