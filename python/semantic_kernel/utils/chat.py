# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, List

from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


def store_results(chat_history: ChatHistory, results: List["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
        if isinstance(message, AzureChatMessageContent) and message.tool_message is not None:
            chat_history.add_tool_message(content=message.tool_message)
        chat_history.add_message(message=message)
    return chat_history
