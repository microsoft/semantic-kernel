# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable

from azure.ai.inference.models import (
    AssistantMessage,
    ChatCompletionsFunctionToolCall,
    ChatRequestMessage,
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

    contentItems = []
    for item in message.items:
        if isinstance(item, TextContent):
            contentItems.append(TextContentItem(text=item.text))
        elif isinstance(item, ImageContent) and (item.data_uri or item.uri):
            contentItems.append(
                ImageContentItem(image_url=ImageUrl(url=item.data_uri or str(item.uri), detail=ImageDetailLevel.Auto))
            )
        else:
            logger.warning(
                "Unsupported item type in User message while formatting chat history for Azure AI"
                f" Inference: {type(item)}"
            )

    return UserMessage(content=contentItems)


def _format_assistant_message(message: ChatMessageContent) -> AssistantMessage:
    """Format an assistant message to the expected object for the client.

    Args:
        message: The assistant message.

    Returns:
        The formatted assistant message.
    """
    contentItems = []
    toolCalls = []

    for item in message.items:
        if isinstance(item, TextContent):
            contentItems.append(TextContentItem(text=item.text))
        elif isinstance(item, FunctionCallContent):
            toolCalls.append(
                ChatCompletionsFunctionToolCall(
                    id=item.id, function=FunctionCall(name=item.name, arguments=item.arguments)
                )
            )
        else:
            logger.warning(
                "Unsupported item type in Assistant message while formatting chat history for Azure AI"
                f" Inference: {type(item)}"
            )

    # tollCalls cannot be an empty list, so we need to set it to None if it is empty
    return AssistantMessage(content=contentItems, tool_calls=toolCalls if toolCalls else None)


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
        logger.warning(
            "Unsupported item type in Tool message while formatting chat history for Azure AI"
            f" Inference: {type(message.items[0])}"
        )

    # The API expects the result to be a string, so we need to convert it to a string
    return ToolMessage(content=str(message.items[0].result), tool_call_id=message.items[0].id)


MESSAGE_CONVERTERS: dict[AuthorRole, Callable[[ChatMessageContent], ChatRequestMessage]] = {
    AuthorRole.SYSTEM: _format_system_message,
    AuthorRole.USER: _format_user_message,
    AuthorRole.ASSISTANT: _format_assistant_message,
    AuthorRole.TOOL: _format_tool_message,
}
