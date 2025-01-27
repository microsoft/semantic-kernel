# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import Callable, Mapping

from azure.ai.inference.models import (
    AssistantMessage,
    ChatCompletionsToolCall,
    ChatRequestMessage,
    ContentItem,
    FunctionCall,
    ImageContentItem,
    ImageDetailLevel,
    ImageUrl,
    SystemMessage,
    TextContentItem,
    ToolMessage,
    UserMessage,
)

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole

logger: logging.Logger = logging.getLogger(__name__)


def _format_system_message(message: ChatMessageContent) -> SystemMessage:
    """Format a system message to the expected object for the client.

    Args:
        message: The system message.

    Returns:
        The formatted system message.
    """
    return SystemMessage(content=message.content)


def _format_developer_message(message: ChatMessageContent) -> ChatRequestMessage:
    """Format a developer message to the expected object for the client.

    Args:
        message: The developer message.

    Returns:
        The formatted developer message.
    """
    # TODO(@ymuichiro): Add support when Azure AI Inference SDK implements developer role
    raise NotImplementedError(
        "Developer role is currently not supported by the Azure AI Inference SDK. "
        "This feature will be implemented in a future update when SDK support is available."
    )


def _format_user_message(message: ChatMessageContent) -> UserMessage:
    """Format a user message to the expected object for the client.

    If there are any image items in the message, we need to create a list of content items,
    otherwise we need to just pass in the content as a string or it will error.

    Args:
        message: The user message.

    Returns:
        The formatted user message.
    """
    if not any(isinstance(item, (ImageContent)) for item in message.items):
        return UserMessage(content=message.content)

    content_items: list[ContentItem] = []
    for item in message.items:
        if isinstance(item, TextContent):
            content_items.append(TextContentItem(text=item.text))
        elif isinstance(item, ImageContent) and (item.data_uri or item.uri):
            content_items.append(
                ImageContentItem(
                    image_url=ImageUrl(url=item.data_uri or str(item.uri), detail=ImageDetailLevel.Auto.value)
                )
            )
        else:
            logger.warning(
                "Unsupported item type in User message while formatting chat history for Azure AI"
                f" Inference: {type(item)}"
            )

    return UserMessage(content=content_items)


def _format_assistant_message(message: ChatMessageContent) -> AssistantMessage:
    """Format an assistant message to the expected object for the client.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message.
    """
    tool_calls: list[ChatCompletionsToolCall] = []

    for item in message.items:
        if isinstance(item, TextContent):
            # Assuming the assistant message will have only one text content item
            # and we assign the content directly to the message content, which is a string.
            continue
        if isinstance(item, FunctionCallContent):
            tool_calls.append(
                ChatCompletionsToolCall(
                    id=item.id or "",
                    function=FunctionCall(
                        name=item.name or "",
                        arguments=json.dumps(item.arguments)
                        if isinstance(item.arguments, Mapping)
                        else item.arguments or "",
                    ),
                )
            )
        else:
            logger.warning(
                "Unsupported item type in Assistant message while formatting chat history for Azure AI"
                f" Inference: {type(item)}"
            )

    # tollCalls cannot be an empty list, so we need to set it to None if it is empty
    return AssistantMessage(content=message.content, tool_calls=tool_calls if tool_calls else None)


def _format_tool_message(message: ChatMessageContent) -> ToolMessage:
    """Format a tool message to the expected object for the client.

    Args:
        message: The tool message.

    Returns:
        The formatted tool message.
    """
    if len(message.items) != 1:
        logger.warning(
            "Unsupported number of items in Tool message while formatting chat history for Azure AI"
            f" Inference: {len(message.items)}"
        )

    if not isinstance(message.items[0], FunctionResultContent):
        raise ValueError("No FunctionResultContent found in the message items")

    # The API expects the result to be a string, so we need to convert it to a string
    return ToolMessage(content=str(message.items[0].result), tool_call_id=message.items[0].id)


MESSAGE_CONVERTERS: dict[AuthorRole, Callable[[ChatMessageContent], ChatRequestMessage]] = {
    AuthorRole.SYSTEM: _format_system_message,
    AuthorRole.USER: _format_user_message,
    AuthorRole.ASSISTANT: _format_assistant_message,
    AuthorRole.TOOL: _format_tool_message,
    AuthorRole.DEVELOPER: _format_developer_message,
}
