# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import Callable, Mapping
from typing import Any

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole

logger: logging.Logger = logging.getLogger(__name__)


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
                "input": item.arguments if isinstance(item.arguments, Mapping) else json.loads(item.arguments or ""),
            })
        else:
            logger.warning(
                f"Unsupported item type in Assistant message while formatting chat history for Anthropic: {type(item)}"
            )

    if tool_calls:
        return {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": message.content,
                },
                *tool_calls,
            ],
        }

    return {
        "role": "assistant",
        "content": message.content,
    }


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
