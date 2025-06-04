# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import (
    BedrockChatPromptExecutionSettings,
    BedrockEmbeddingPromptExecutionSettings,
    BedrockTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidResponseError

# region Text Completion


def get_text_completion_request_body(prompt: str, settings: BedrockTextPromptExecutionSettings) -> Any:
    """Get the request body for text completion for Amazon Titan models.

    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html
    """
    return remove_none_recursively({
        "inputText": prompt,
        "textGenerationConfig": {
            "temperature": settings.temperature,
            "topP": settings.top_p,
            "maxTokenCount": settings.max_tokens,
            "stopSequences": settings.stop,
        },
    })


def parse_text_completion_response(response: dict[str, Any], model_id: str) -> list[TextContent]:
    """Parse the response from text completion for Amazon Titan models."""
    prompt_tokens = response.get("inputTextTokenCount")
    return [
        TextContent(
            ai_model_id=model_id,
            text=completion["outputText"],
            inner_content=completion,
            metadata={
                "usage": CompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=response.get("tokenCount"),
                )
            },
        )
        for completion in response.get("results", [])
        if "outputText" in completion
    ]


def parse_streaming_text_completion_response(chunk: dict[str, Any], model_id: str) -> StreamingTextContent:
    """Parse the response from streaming text completion for Amazon Titan models."""
    return StreamingTextContent(
        choice_index=0,
        ai_model_id=model_id,
        text=chunk["outputText"],
        inner_content=chunk,
        metadata={
            "usage": CompletionUsage(
                prompt_tokens=chunk.get("inputTextTokenCount"),
                completion_tokens=chunk.get("totalOutputTextTokenCount"),
            )
        },
    )


# endregion

# region Chat Completion


def get_chat_completion_additional_model_request_fields(
    settings: BedrockChatPromptExecutionSettings,
) -> dict[str, Any] | None:
    """Get the additional model request fields for chat completion for Amazon Titan models.

    Amazon Titan models do not support additional model request fields.
    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html
    """
    return None


# endregion

# region Text Embedding


def get_text_embedding_request_body(text: str, settings: BedrockEmbeddingPromptExecutionSettings) -> dict[str, Any]:
    """Get the request body for text embedding for Amazon Titan models."""
    return remove_none_recursively({
        "inputText": text,
        # Extension data: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-embed-text.html
        "dimensions": settings.extension_data.get("dimensions", None),
        "normalize": settings.extension_data.get("normalize", None),
        "embeddingTypes": settings.extension_data.get("embeddingTypes", None),
        # Extension data: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-embed-mm.html
        "embeddingConfig": settings.extension_data.get("embeddingConfig", None),
    })


def parse_text_embedding_response(response: dict[str, Any]) -> list[float]:
    """Parse the response from text embedding for Amazon Titan models."""
    if "embedding" not in response or not isinstance(response["embedding"], list):
        raise ServiceInvalidResponseError("The response from Amazon Titan model does not contain embeddings.")

    return response.get("embedding")  # type: ignore


# endregion
