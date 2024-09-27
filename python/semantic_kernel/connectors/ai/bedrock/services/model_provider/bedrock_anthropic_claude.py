# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.contents.text_content import TextContent


def get_text_completion_request_body(prompt: str, settings: BedrockTextPromptExecutionSettings) -> Any:
    """Get the request body for text completion for Anthropic Claude models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-text-completion.html
    """
    return remove_none_recursively({
        "prompt": prompt,
        "temperature": settings.temperature,
        "top_p": settings.top_p,
        "top_k": settings.top_k,
        "max_tokens_to_sample": settings.max_tokens,
        "stop_sequences": settings.stop,
    })


def parse_text_completion_response(response: dict[str, Any], model_id: str) -> list[TextContent]:
    """Parse the response from text completion for Anthropic Claude models."""
    return [
        TextContent(
            ai_model_id=model_id,
            text=response.get("completion", ""),
            inner_content=response,
        )
    ]
