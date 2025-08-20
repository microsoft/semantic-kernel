# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


def store_results(
        chat_history: ChatHistory, 
        results: list["ChatMessageContent"]) -> ChatHistory:
    """Stores specific results in the context and chat prompt.

    Args:
        chat_history(ChatHistory): The current chat history instance.
        results(list["ChatMessageContent"]): Messages to be stored in the history.

    Returns:
        ChatHistory: Updated chat history containing the new messages.
    """
    for message in results:
        chat_history.add_message(message=message)
    return chat_history
