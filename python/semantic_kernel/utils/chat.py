# Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from typing import TYPE_CHECKING

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from typing import TYPE_CHECKING

=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
from typing import TYPE_CHECKING

=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from typing import TYPE_CHECKING

=======
from typing import TYPE_CHECKING, List

from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
def store_results(chat_history: ChatHistory, results: list["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
def store_results(chat_history: ChatHistory, results: list["ChatMessageContent"]):
    """Stores specific results in the context and chat prompt."""
    for message in results:
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        chat_history.add_message(message=message)
    return chat_history
