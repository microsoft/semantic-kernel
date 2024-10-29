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
    """Get the request body for text completion for Mistral AI models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-mistral-text-completion.html
    """
    return remove_none_recursively({
        "prompt": f"<s>[INST] {prompt} [/INST]",
        "max_tokens": settings.max_tokens,
        "stop": settings.stop,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "top_k": settings.top_k,
    })


def parse_text_completion_response(response: dict[str, Any], model_id: str) -> list[TextContent]:
    """Parse the response from text completion for AI21 Labs models."""
    return [
        TextContent(
            ai_model_id=model_id,
            text=output["text"],
            inner_content=output,
        )
        for output in response.get("outputs", [])
    ]


# endregion


# region Chat Completion


def get_chat_completion_additional_model_request_fields(
    settings: BedrockChatPromptExecutionSettings,
) -> dict[str, Any] | None:
    """Get the additional model request fields for chat completion for Mistral AI models.

    MMistral AI models do not support additional model request fields.
    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-mistral-chat-completion.html
    """
    return None


# endregion
