# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import (
    BedrockChatPromptExecutionSettings,
    BedrockEmbeddingPromptExecutionSettings,
    BedrockTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidResponseError

# region Text Completion


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


# endregion

# region Chat Completion


def get_chat_completion_additional_model_request_fields(
    settings: BedrockChatPromptExecutionSettings,
) -> dict[str, Any] | None:
    """Get the additional model request fields for chat completion for Cohere Command models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command-r-plus.html
    """
    additional_fields: dict[str, Any] = remove_none_recursively({
        "search_queries_only": settings.search_queries_only if hasattr(settings, "search_queries_only") else None,
        "preamble": settings.preamble if hasattr(settings, "preamble") else None,
        "prompt_truncation": settings.prompt_truncation if hasattr(settings, "prompt_truncation") else None,
        "frequency_penalty": settings.frequency_penalty if hasattr(settings, "frequency_penalty") else None,
        "presence_penalty": settings.presence_penalty if hasattr(settings, "presence_penalty") else None,
        "seed": settings.seed if hasattr(settings, "seed") else None,
        "return_prompt": settings.return_prompt if hasattr(settings, "return_prompt") else None,
        "raw_prompting": settings.raw_prompting if hasattr(settings, "raw_prompting") else None,
    })

    if not additional_fields:
        return None

    return additional_fields


# endregion

# region Text Embedding


def get_text_embedding_request_body(text: str, settings: BedrockEmbeddingPromptExecutionSettings) -> Any:
    """Get the request body for text embedding for Cohere Command models."""
    return remove_none_recursively({
        "texts": [text],
        "input_type": settings.input_type if hasattr(settings, "input_type") else "search_document",
        "truncate": settings.truncate if hasattr(settings, "truncate") else None,
        "embedding_types": settings.embedding_types if hasattr(settings, "embedding_types") else None,
    })


def parse_text_embedding_response(response: dict[str, Any]) -> list[float]:
    """Parse the response from text embedding for Cohere Command models."""
    if "embeddings" not in response or not isinstance(response["embeddings"], list) or len(response["embeddings"]) == 0:
        raise ServiceInvalidResponseError("The response from Cohere model does not contain embeddings.")

    return response.get("embeddings")[0]  # type: ignore


# endregion
