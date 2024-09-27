# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.contents.text_content import TextContent


def get_text_completion_request_body(prompt: str, settings: BedrockTextPromptExecutionSettings) -> Any:
    """Get the request body for text completion for Cohere Command models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command.html
    """
    return remove_none_recursively({
        "prompt": prompt,
        "temperature": settings.temperature,
        "p": settings.top_p,
        "k": settings.top_k,
        "max_tokens": settings.max_tokens,
        "stop_sequences": settings.stop,
        # Extension data
        "return_likelihoods": settings.return_likelihoods if hasattr(settings, "return_likelihoods") else "NONE",
        "num_generations": settings.num_generations if hasattr(settings, "num_generations") else 1,
        "logit_bias": settings.logit_bias if hasattr(settings, "logit_bias") else None,
        "truncate": settings.truncate if hasattr(settings, "truncate") else "NONE",
    })


def parse_text_completion_response(response: dict[str, Any], model_id: str) -> list[TextContent]:
    """Parse the response from text completion for Anthropic Claude models."""
    return [
        TextContent(
            ai_model_id=model_id,
            text=generation["text"],
            inner_content=generation,
        )
        for generation in response.get("generations", [])
    ]
