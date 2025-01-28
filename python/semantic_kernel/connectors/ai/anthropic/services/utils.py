# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger: logging.Logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def _format_user_message(message: ChatMessageContent) -> dict[str, Any]:
    """Format a user message to the expected object for the Anthropic client.

    Args:
        message: The user message.

    Returns:
        The formatted user message.
    """
    return {
        "role": "user",
        "content": message.content,
    }


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
            "properties": {p.name: p.schema_data for p in metadata.parameters},
            "required": [p.name for p in metadata.parameters if p.is_required],
        },
    }
