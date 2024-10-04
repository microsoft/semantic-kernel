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
        "countPenalty": settings.countPenalty if hasattr(settings, "countPenalty") else None,
        "presencePenalty": settings.presencePenalty if hasattr(settings, "presencePenalty") else None,
        "frequencyPenalty": settings.frequencyPenalty if hasattr(settings, "frequencyPenalty") else None,
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
    """
    additional_fields: dict[str, Any] = remove_none_recursively({
        # TODO(taochen@microsoft.com): verify what a response that contains multiple completions looks like
        "n": settings.n if hasattr(settings, "n") else None,
        "frequency_penalty": settings.frequency_penalty if hasattr(settings, "frequency_penalty") else None,
        "presence_penalty": settings.presence_penalty if hasattr(settings, "presence_penalty") else None,
    })

    if not additional_fields:
        return None

    return additional_fields


# endregion
