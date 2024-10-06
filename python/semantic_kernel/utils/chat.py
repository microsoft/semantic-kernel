# Copyright (c) Microsoft. All rights reserved.

<<<<<<< Updated upstream
from typing import TYPE_CHECKING

=======
<<<<<<< HEAD
from typing import TYPE_CHECKING

=======
<<<<<<< HEAD
from typing import TYPE_CHECKING

=======
from typing import TYPE_CHECKING, List

from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


<<<<<<< Updated upstream
def store_results(chat_history: ChatHistory, results: list["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
=======
<<<<<<< HEAD
def store_results(chat_history: ChatHistory, results: list["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
=======
<<<<<<< HEAD
def store_results(chat_history: ChatHistory, results: list["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
=======
def store_results(chat_history: ChatHistory, results: List["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
        if isinstance(message, AzureChatMessageContent) and message.tool_message is not None:
            chat_history.add_tool_message(content=message.tool_message)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
>>>>>>> Stashed changes
        chat_history.add_message(message=message)
    return chat_history
