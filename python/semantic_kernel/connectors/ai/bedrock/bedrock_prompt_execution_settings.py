# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class BedrockPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Prompt Execution Settings."""

    ...


class BedrockChatPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Chat Prompt Execution Settings."""

    ...


class BedrockTextPromptExecutionSettings(BedrockPromptExecutionSettings):
    """Bedrock Text Prompt Execution Settings."""

    ...


class BedrockEmbeddingPromptExecutionSettings(PromptExecutionSettings):
    """Bedrock Embedding Prompt Execution Settings."""

    ...
