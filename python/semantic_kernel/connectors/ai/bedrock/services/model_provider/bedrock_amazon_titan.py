# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockTextPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.model_provider.utils import remove_none_recursively
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent


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
