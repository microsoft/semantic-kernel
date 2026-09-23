# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings

# region Chat Completion


def get_chat_completion_additional_model_request_fields(
    settings: BedrockChatPromptExecutionSettings,
) -> dict[str, Any] | None:
    """Get the additional model request fields for chat completion for OpenAI models.

    OpenAI models do not need additional model request fields.
    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-openai.html
    """
    return None


# endregion
