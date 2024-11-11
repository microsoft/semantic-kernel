# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import (
    BedrockChatPromptExecutionSettings,
    BedrockTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.contents.text_content import TextContent

# region Text Completion


def get_text_completion_request_body(prompt: str, settings: BedrockTextPromptExecutionSettings) -> Any:
    """Get the request body for text completion for AI21 Labs models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jurassic2.html
    """
    return remove_none_recursively({
        "prompt": prompt,
        "temperature": settings.temperature,
        "topP": settings.top_p,
        "maxTokens": settings.max_tokens,
        "stopSequences": settings.stop,
        # Extension data
        "countPenalty": settings.extension_data.get("countPenalty", None),
        "presencePenalty": settings.extension_data.get("presencePenalty", None),
        "frequencyPenalty": settings.extension_data.get("frequencyPenalty", None),
    })


def parse_text_completion_response(response: dict[str, Any], model_id: str) -> list[TextContent]:
    """Parse the response from text completion for AI21 Labs models."""
    return [
        TextContent(
            ai_model_id=model_id,
            text=completion["data"]["text"],
            inner_content=completion,
        )
        for completion in response.get("completions", [])
    ]


# endregion


# region Chat Completion


def get_chat_completion_additional_model_request_fields(
    settings: BedrockChatPromptExecutionSettings,
) -> dict[str, Any] | None:
    """Get the additional model request fields for chat completion for AI21 Labs models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jamba.html
    Note: We are not supporting multiple responses for now.
    """
    additional_fields: dict[str, Any] = remove_none_recursively({
        "frequency_penalty": settings.extension_data.get("frequency_penalty", None),
        "presence_penalty": settings.extension_data.get("presence_penalty", None),
    })

    if not additional_fields:
        return None

    return additional_fields


# endregion
