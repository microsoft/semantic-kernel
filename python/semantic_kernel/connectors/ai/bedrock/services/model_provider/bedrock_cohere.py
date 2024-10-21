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
        "return_likelihoods": settings.extension_data.get("return_likelihoods", "NONE"),
        "num_generations": settings.extension_data.get("num_generations", 1),
        "logit_bias": settings.extension_data.get("logit_bias", None),
        "truncate": settings.extension_data.get("truncate", "NONE"),
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
        "search_queries_only": settings.extension_data.get("search_queries_only", None),
        "preamble": settings.extension_data.get("preamble", None),
        "prompt_truncation": settings.extension_data.get("prompt_truncation", None),
        "frequency_penalty": settings.extension_data.get("frequency_penalty", None),
        "presence_penalty": settings.extension_data.get("presence_penalty", None),
        "seed": settings.extension_data.get("seed", None),
        "return_prompt": settings.extension_data.get("return_prompt", None),
        "raw_prompting": settings.extension_data.get("raw_prompting", None),
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
        "input_type": settings.extension_data.get("input_type", "search_document"),
        "truncate": settings.extension_data.get("truncate", None),
        "embedding_types": settings.extension_data.get("embedding_types", None),
    })


def parse_text_embedding_response(response: dict[str, Any]) -> list[float]:
    """Parse the response from text embedding for Cohere Command models."""
    if "embeddings" not in response or not isinstance(response["embeddings"], list) or len(response["embeddings"]) == 0:
        raise ServiceInvalidResponseError("The response from Cohere model does not contain embeddings.")

    return response.get("embeddings")[0]  # type: ignore


# endregion
