# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated, Any

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class BedrockPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Prompt Execution Settings."""

    temperature: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    top_k: Annotated[int | None, Field(gt=0)] = None
    max_tokens: Annotated[int | None, Field(gt=0)] = None
    stop: list[str] = Field(default_factory=list)


class BedrockChatPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Chat Prompt Execution Settings."""

    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    tool_choice: Annotated[
        dict[str, Any] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None


class BedrockTextPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Text Prompt Execution Settings."""

    ...


class BedrockEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Embedding Prompt Execution Settings."""

    ...
