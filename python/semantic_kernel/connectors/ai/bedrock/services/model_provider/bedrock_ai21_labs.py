# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.contents.text_content import TextContent


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
