# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Any

from google.generativeai.protos import Blob, Candidate, FunctionResponse, Part

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionCallChoiceConfiguration, FunctionChoiceType
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger: logging.Logger = logging.getLogger(__name__)


def finish_reason_from_google_ai_to_semantic_kernel(
    finish_reason: Candidate.FinishReason,
) -> SemanticKernelFinishReason | None:
    """Convert a Google AI FinishReason to a Semantic Kernel FinishReason.

    This is best effort and may not cover all cases as the enums are not identical.
    """
    if finish_reason == Candidate.FinishReason.STOP:
        return SemanticKernelFinishReason.STOP

    if finish_reason == Candidate.FinishReason.MAX_TOKENS:
        return SemanticKernelFinishReason.LENGTH

    if finish_reason == Candidate.FinishReason.SAFETY:
        return SemanticKernelFinishReason.CONTENT_FILTER

    return None


def filter_system_message(chat_history: ChatHistory) -> str | None:
    """Filter the first system message from the chat history.

    If there are multiple system messages, raise an error.
    If there are no system messages, return None.
    """
    if len([message for message in chat_history if message.role == AuthorRole.SYSTEM]) > 1:
        raise ServiceInvalidRequestError(
            "Multiple system messages in chat history. Only one system message is expected."
        )

    for message in chat_history:
        if message.role == AuthorRole.SYSTEM:
            return message.content

    return None


def format_user_message(message: ChatMessageContent) -> list[Part]:
    """Format a user message to the expected object for the client.

    Args:
        message: The user message.

    Returns:
        The formatted user message as a list of parts.
    """
    if not any(isinstance(item, (ImageContent)) for item in message.items):
        return [Part(text=message.content)]

    parts: list[Part] = []
    for item in message.items:
        if isinstance(item, TextContent):
            parts.append(Part(text=message.content))
        elif isinstance(item, ImageContent):
            if item.data_uri:
                parts.append(Part(inline_data=Blob(mime_type=item.mime_type, data=item.data)))
            else:
                # The Google AI API doesn't support image from an arbitrary URI:
                # https://github.com/google-gemini/generative-ai-python/issues/357
                raise ServiceInvalidRequestError(
                    "ImageContent without data_uri in User message while formatting chat history for Google AI"
                )
        else:
            raise ServiceInvalidRequestError(
                "Unsupported item type in User message while formatting chat history for Google AI"
                f" Inference: {type(item)}"
            )

    return parts


def format_assistant_message(message: ChatMessageContent) -> list[Part]:
    """Format an assistant message to the expected object for the client.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message as a list of parts.
    """
    return [Part(text=message.content)]


def format_tool_message(message: ChatMessageContent) -> list[Part]:
    """Format a tool message to the expected object for the client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    if len(message.items) != 1:
        logger.warning(
            "Unsupported number of items in Tool message while formatting chat history for Google AI: "
            f"{len(message.items)}"
        )

    if not isinstance(message.items[0], FunctionResultContent):
        raise ValueError("No FunctionResultContent found in the message items")

    gemini_function_name = format_function_result_content_name_to_gemini_function_name(message.items[0])

    return [
        Part(
            function_response=FunctionResponse(
                name=gemini_function_name,
                response={
                    "name": gemini_function_name,
                    "content": json.dumps(message.items[0].result),
                },
            )
        )
    ]


_FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE = {
    FunctionChoiceType.AUTO: "AUTO",
    FunctionChoiceType.NONE: "NONE",
    FunctionChoiceType.REQUIRED: "ANY",
}

# The separator used in the fully qualified name of the function instead of the default "-" separator.
# This is required since Gemini doesn't work well with "-" in the function name.
# https://ai.google.dev/gemini-api/docs/function-calling#function_declarations
GEMINI_FUNCTION_NAME_SEPARATOR = "_"


def format_function_result_content_name_to_gemini_function_name(function_result_content: FunctionResultContent) -> str:
    """Format the function result content name to the Gemini function name."""
    return (
        f"{function_result_content.plugin_name}{GEMINI_FUNCTION_NAME_SEPARATOR}{function_result_content.function_name}"
        if function_result_content.plugin_name
        else function_result_content.function_name
    )


def format_kernel_function_fully_qualified_name_to_gemini_function_name(metadata: KernelFunctionMetadata) -> str:
    """Format the kernel function fully qualified name to the Gemini function name."""
    return (
        f"{metadata.plugin_name}{GEMINI_FUNCTION_NAME_SEPARATOR}{metadata.name}"
        if metadata.plugin_name
        else metadata.name
    )


def format_gemini_function_name_to_kernel_function_fully_qualified_name(gemini_function_name: str) -> str:
    """Format the Gemini function name to the kernel function fully qualified name."""
    if GEMINI_FUNCTION_NAME_SEPARATOR in gemini_function_name:
        plugin_name, function_name = gemini_function_name.split(GEMINI_FUNCTION_NAME_SEPARATOR, 1)
        return f"{plugin_name}-{function_name}"
    return gemini_function_name


def kernel_function_metadata_to_google_function_call_format(metadata: KernelFunctionMetadata) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "name": format_kernel_function_fully_qualified_name_to_gemini_function_name(metadata),
        "description": metadata.description or "",
        "parameters": {
            "type": "object",
            "properties": {param.name: param.schema_data for param in metadata.parameters},
            "required": [p.name for p in metadata.parameters if p.is_required],
        },
    }


def update_settings_from_function_choice_configuration(
    function_choice_configuration: FunctionCallChoiceConfiguration,
    settings: GoogleAIChatPromptExecutionSettings,
    type: FunctionChoiceType,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    if function_choice_configuration.available_functions:
        settings.tool_config = {
            "function_calling_config": {
                "mode": _FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[type],
            }
        }
        settings.tools = [
            {
                "function_declarations": [
                    kernel_function_metadata_to_google_function_call_format(f)
                    for f in function_choice_configuration.available_functions
                ]
            }
        ]
