# Copyright (c) Microsoft. All rights reserved.

import base64
import json
import logging
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger: logging.Logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


# Image media types accepted by the Anthropic API.
_SUPPORTED_IMAGE_MEDIA_TYPES = ("image/png", "image/jpeg", "image/gif", "image/webp")

# Magic numbers of the image formats supported by the Anthropic API.
_IMAGE_MAGIC_NUMBERS: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)


def _detect_image_media_type(data: bytes | str) -> str | None:
    """Detect the media type of an image from its magic number.

    Args:
        data: The raw image data.

    Returns:
        A media type supported by Anthropic, or None when the data is not a
        recognized image.
    """
    if not isinstance(data, bytes):
        return None
    for magic, media_type in _IMAGE_MAGIC_NUMBERS:
        if data.startswith(magic):
            return media_type
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _format_user_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format a user message to the expected object for the Anthropic client.

    A text-only message keeps its historical string content. When the message
    carries images, all items are converted to Anthropic content blocks so
    that images are not silently dropped and an image-only message remains a
    valid request. The media type of an image is taken from its MIME type when
    supported, otherwise detected from the data; images with an unsupported or
    undetectable media type are skipped with a warning.

    Args:
        message: The user message.

    Returns:
        The formatted user message.
    """
    if not any(isinstance(item, ImageContent) for item in message.items):
        return {
            "role": "user",
            "content": message.content,
        }

    blocks: list[dict[str, Any]] = []
    for item in message.items:
        if isinstance(item, TextContent):
            if item.text:
                blocks.append({"type": "text", "text": item.text})
        elif isinstance(item, ImageContent):
            if item.data:
                data = item.data
                media_type = (
                    item.mime_type if item.mime_type in _SUPPORTED_IMAGE_MEDIA_TYPES else _detect_image_media_type(data)
                )
                if media_type is None:
                    logger.warning(
                        "Skipping ImageContent with an unsupported or undetectable media type "
                        "while formatting a user message for Anthropic."
                    )
                    continue
                if isinstance(data, bytes):
                    data = base64.b64encode(data).decode("ascii")
                blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": data,
                    },
                })
            elif item.uri:
                blocks.append({
                    "type": "image",
                    "source": {"type": "url", "url": str(item.uri)},
                })
            else:
                logger.warning(
                    "Skipping ImageContent with neither data nor URI while formatting a user message for Anthropic."
                )
        else:
            logger.warning(
                f"Unsupported item type in User message while formatting chat history for Anthropic: {type(item)}"
            )

    return {"role": "user", "content": blocks}


def _format_assistant_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format an assistant message to the expected object for the Anthropic client.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message.
    """
    tool_calls: list[dict[str, Any]] = []

    for item in message.items:
        if isinstance(item, TextContent):
            # Assuming the assistant message will have only one text content item
            # and we assign the content directly to the message content, which is a string.
            continue
        if isinstance(item, FunctionCallContent):
            tool_calls.append({
                "type": "tool_use",
                "id": item.id or "",
                "name": item.name or "",
                "input": item.arguments
                if isinstance(item.arguments, Mapping)
                else json.loads(item.arguments)
                if item.arguments
                else {},
            })
        else:
            logger.warning(
                f"Unsupported item type in Assistant message while formatting chat history for Anthropic: {type(item)}"
            )

    formatted_message: dict[str, Any] = {"role": "assistant", "content": []}

    if message.content:
        # Only include the text content if it is not empty.
        # Otherwise, the Anthropic client will throw an error.
        formatted_message["content"].append({  # type: ignore
            "type": "text",
            "text": message.content,
        })
    if tool_calls:
        # Only include the tool calls if there are any.
        # Otherwise, the Anthropic client will throw an error.
        formatted_message["content"].extend(tool_calls)  # type: ignore

    return formatted_message


def _format_tool_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format a tool message to the expected object for the Anthropic client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    function_result_contents: list[dict[str, Any]] = []
    for item in message.items:
        if not isinstance(item, FunctionResultContent):
            logger.warning(
                f"Unsupported item type in Tool message while formatting chat history for Anthropic: {type(item)}"
            )
            continue
        function_result_contents.append({
            "type": "tool_result",
            "tool_use_id": item.id,
            "content": str(item.result),
        })

    return {
        "role": "user",
        "content": function_result_contents,
    }


MESSAGE_CONVERTERS: dict[AuthorRole, Callable[[ChatMessageContent], dict[str, Any]]] = {
    AuthorRole.USER: _format_user_message,
    AuthorRole.ASSISTANT: _format_assistant_message,
    AuthorRole.TOOL: _format_tool_message,
}


def update_settings_from_function_call_configuration(
    function_choice_configuration: "FunctionCallChoiceConfiguration",
    settings: "PromptExecutionSettings",
    type: FunctionChoiceType,
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    if (
        function_choice_configuration.available_functions
        and hasattr(settings, "tools")
        and hasattr(settings, "tool_choice")
    ):
        settings.tools = [
            kernel_function_metadata_to_function_call_format(f)
            for f in function_choice_configuration.available_functions
        ]

        if (
            settings.function_choice_behavior and settings.function_choice_behavior.type_ == FunctionChoiceType.REQUIRED
        ) or type == FunctionChoiceType.REQUIRED:
            settings.tool_choice = {"type": "any"}
        else:
            settings.tool_choice = {"type": type.value}


def kernel_function_metadata_to_function_call_format(metadata: KernelFunctionMetadata) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "name": metadata.fully_qualified_name,
        "description": metadata.description or "",
        "input_schema": {
            "type": "object",
            "properties": {p.name: p.schema_data for p in metadata.parameters if p.include_in_function_choices},
            "required": [p.name for p in metadata.parameters if p.is_required and p.include_in_function_choices],
        },
    }
