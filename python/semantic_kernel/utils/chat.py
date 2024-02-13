# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, List, Optional, Tuple

from semantic_kernel.models.ai.chat_completion.chat_history import ChatHistory

# def prepare_chat_history_for_request_for_request(
#     chat_history: ChatHistory,
# ) -> List[Dict[str, str]]:
#     """Prepare the chat history for a request."""
#     return [{"role": message.role, "content": message.content} for message in chat_history.messages]

def prepare_chat_history_for_request(
    chat_history: ChatHistory,
    output_role_key: str = "role",  # Default to "role", change to "author" as needed
    override_role: Optional[str] = None,  # Default to None, change to "user" as needed
) -> List[Dict[str, str]]:
    """
    Prepare the chat history for a request, allowing customization of the key names for role/author,
    and optionally overriding the role.

    :param chat_history: ChatHistory object containing the chat messages.
    :param output_role_key: The key name to use for the role/author field in the output.
    :param override_role: Optional string to override the role in all messages. If None, use the original role.
    :return: A list of message dictionaries formatted as per the specified keys and optional role override.
    """
    return [
        {output_role_key: override_role if override_role else message.role, "content": message.content}
        for message in chat_history.messages
    ]