# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from enum import Enum
from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider import (
    bedrock_ai21_labs,
    bedrock_amazon_titan,
    bedrock_anthropic_claude,
    bedrock_cohere,
    bedrock_meta_llama,
    bedrock_mistralai,
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent


class BedrockModelProvider(Enum):
    """Amazon Bedrock Model Provider Enum.

    This list contains the providers of all base models available on Amazon Bedrock.
    """

    AI21LABS = "ai21"
    AMAZON = "amazon"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    META = "meta"
    MISTRALAI = "mistral"

    @classmethod
    def to_model_provider(cls, model_id: str) -> "BedrockModelProvider":
        """Convert a model ID to a model provider."""
        provider = model_id.split(".")[0]
        return cls(provider)


# region Text Completion


TEXT_COMPLETION_REQUEST_BODY_MAPPING: dict[
    BedrockModelProvider, Callable[[str, BedrockTextPromptExecutionSettings], Any]
] = {
    BedrockModelProvider.AMAZON: bedrock_amazon_titan.get_text_completion_request_body,
    BedrockModelProvider.ANTHROPIC: bedrock_anthropic_claude.get_text_completion_request_body,
    BedrockModelProvider.COHERE: bedrock_cohere.get_text_completion_request_body,
    BedrockModelProvider.AI21LABS: bedrock_ai21_labs.get_text_completion_request_body,
    BedrockModelProvider.META: bedrock_meta_llama.get_text_completion_request_body,
    BedrockModelProvider.MISTRALAI: bedrock_mistralai.get_text_completion_request_body,
}

TEXT_COMPLETION_RESPONSE_MAPPING: dict[BedrockModelProvider, Callable[[dict[str, Any], str], list[TextContent]]] = {
    BedrockModelProvider.AMAZON: bedrock_amazon_titan.parse_text_completion_response,
    BedrockModelProvider.ANTHROPIC: bedrock_anthropic_claude.parse_text_completion_response,
    BedrockModelProvider.COHERE: bedrock_cohere.parse_text_completion_response,
    BedrockModelProvider.AI21LABS: bedrock_ai21_labs.parse_text_completion_response,
    BedrockModelProvider.META: bedrock_meta_llama.parse_text_completion_response,
    BedrockModelProvider.MISTRALAI: bedrock_mistralai.parse_text_completion_response,
}

STREAMING_TEXT_COMPLETION_RESPONSE_MAPPING: dict[
    BedrockModelProvider, Callable[[dict[str, Any], str], StreamingTextContent]
] = {
    BedrockModelProvider.AMAZON: bedrock_amazon_titan.parse_streaming_text_completion_response,
}


def get_text_completion_request_body(model_id: str, prompt: str, settings: BedrockTextPromptExecutionSettings) -> dict:
    """Get the request body for text completion for Amazon Bedrock models."""
    model_provider = BedrockModelProvider.to_model_provider(model_id)
    return TEXT_COMPLETION_REQUEST_BODY_MAPPING[model_provider](prompt, settings)


def parse_text_completion_response(model_id: str, response: dict) -> list[TextContent]:
    """Parse the response from text completion for Amazon Bedrock models."""
    model_provider = BedrockModelProvider.to_model_provider(model_id)
    return TEXT_COMPLETION_RESPONSE_MAPPING[model_provider](response, model_id)


def parse_streaming_text_completion_response(model_id: str, chunk: dict) -> StreamingTextContent:
    """Parse the response from streaming text completion for Amazon Bedrock models."""
    model_provider = BedrockModelProvider.to_model_provider(model_id)
    return STREAMING_TEXT_COMPLETION_RESPONSE_MAPPING[model_provider](chunk, model_id)


# endregion
