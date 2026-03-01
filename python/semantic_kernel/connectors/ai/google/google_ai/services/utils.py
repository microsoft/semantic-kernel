# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import TYPE_CHECKING, Any

from google.genai.types import FinishReason, Part

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.shared_utils import (
    FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE,
    GEMINI_FUNCTION_NAME_SEPARATOR,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


def finish_reason_from_google_ai_to_semantic_kernel(
    finish_reason: FinishReason | None,
) -> SemanticKernelFinishReason | None:
    """Convert a Google AI FinishReason to a Semantic Kernel FinishReason.

    This is best effort and may not cover all cases as the enums are not identical.
    """
    if finish_reason is None:
        return None

    if finish_reason == FinishReason.STOP:
        return SemanticKernelFinishReason.STOP

    if finish_reason == FinishReason.MAX_TOKENS:
        return SemanticKernelFinishReason.LENGTH

    if finish_reason == FinishReason.SAFETY:
        return SemanticKernelFinishReason.CONTENT_FILTER

    return None


def format_user_message(message: ChatMessageContent) -> list[Part]:
    """Format a user message to the expected object for the client.

    Args:
        message: The user message.

    Returns:
        The formatted user message as a list of parts.
    """
    parts: list[Part] = []
    for item in message.items:
        if isinstance(item, TextContent):
            parts.append(Part.from_text(text=item.text))
        elif isinstance(item, ImageContent):
            parts.append(_create_image_part(item))
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
    parts: list[Part] = []
    for item in message.items:
        if isinstance(item, TextContent):
            if item.text:
                parts.append(Part.from_text(text=item.text))
        elif isinstance(item, FunctionCallContent):
            thought_signature = item.metadata.get("thought_signature") if item.metadata else None
            if thought_signature:
                parts.append(
                    Part(
                        function_call={
                            "name": item.name,
                            "args": json.loads(item.arguments)
                            if isinstance(item.arguments, str)
                            else item.arguments,
                        },
                        thought_signature=thought_signature,
                    )
                )
            else:
                parts.append(
                    Part.from_function_call(
                        name=item.name,  # type: ignore[arg-type]
                        args=json.loads(item.arguments) if isinstance(item.arguments, str) else item.arguments,  # type: ignore[arg-type]
                    )
                )
        elif isinstance(item, ImageContent):
            parts.append(_create_image_part(item))
        else:
            raise ServiceInvalidRequestError(
                "Unsupported item type in Assistant message while formatting chat history for Google AI"
                f" Inference: {type(item)}"
            )

    return parts


def format_tool_message(message: ChatMessageContent) -> list[Part]:
    """Format a tool message to the expected object for the client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    parts: list[Part] = []
    for item in message.items:
        if isinstance(item, FunctionResultContent):
            gemini_function_name = item.custom_fully_qualified_name(GEMINI_FUNCTION_NAME_SEPARATOR)
            parts.append(
                Part.from_function_response(
                    name=gemini_function_name,
                    response={
                        "content": str(item.result),
                    },
                )
            )

    return parts


def kernel_function_metadata_to_google_ai_function_call_format(metadata: KernelFunctionMetadata) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "name": metadata.custom_fully_qualified_name(GEMINI_FUNCTION_NAME_SEPARATOR),
        "description": metadata.description or "",
        "parameters": {
            "type": "object",
            "properties": {param.name: param.schema_data for param in metadata.parameters},
            "required": [p.name for p in metadata.parameters if p.is_required],
        }
        if metadata.parameters
        else None,
    }


def update_settings_from_function_choice_configuration(
    function_choice_configuration: "FunctionCallChoiceConfiguration",
    settings: "PromptExecutionSettings",
    type: FunctionChoiceType,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    assert isinstance(settings, GoogleAIChatPromptExecutionSettings)  # nosec

    if function_choice_configuration.available_functions:
        settings.tool_config = {
            "function_calling_config": {
                "mode": FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE[type],
            }
        }
        settings.tools = [
            {
                "function_declarations": [
                    kernel_function_metadata_to_google_ai_function_call_format(f)
                    for f in function_choice_configuration.available_functions
                ]
            }
        ]


def _create_image_part(image_content: ImageContent) -> Part:
    if image_content.data_uri:
        return Part.from_bytes(data=image_content.data, mime_type=image_content.mime_type)  # type: ignore[arg-type]

    # The Google AI API doesn't support images from arbitrary URIs:
    # https://github.com/google-gemini/generative-ai-python/issues/357
    raise ServiceInvalidRequestError(
        "ImageContent without data_uri in User message while formatting chat history for Google AI"
    )
