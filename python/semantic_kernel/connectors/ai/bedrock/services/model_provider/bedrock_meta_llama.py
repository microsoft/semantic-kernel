# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents.text_content import TextContent


def get_text_completion_request_body(prompt: str, settings: BedrockTextPromptExecutionSettings) -> Any:
    """Get the request body for text completion for AI21 Labs models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jurassic2.html
    """
    return remove_none_recursively({
        "prompt": prompt,
        "temperature": settings.temperature,
        "topP": settings.top_p,
        "max_gen_len": settings.max_tokens,
    })


def parse_text_completion_response(response: dict[str, Any], model_id: str) -> list[TextContent]:
    """Parse the response from text completion for AI21 Labs models."""
    return [
        TextContent(
            ai_model_id=model_id,
            text=response["generation"],
            inner_content=response,
            metadata={
                "usage": CompletionUsage(
                    prompt_tokens=response.get("prompt_token_count"),
                    completion_tokens=response.get("completion_token_count"),
                )
            },
        )
    ]
