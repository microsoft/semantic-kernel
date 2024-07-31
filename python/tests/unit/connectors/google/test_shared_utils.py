# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.google.shared_utils import filter_system_message
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidRequestError


def test_first_system_message():
    """Test filter_system_message."""
    # Test with a single system message
    chat_history = ChatHistory()
    chat_history.add_system_message("System message")
    chat_history.add_user_message("User message")
    assert filter_system_message(chat_history) == "System message"

    # Test with no system message
    chat_history = ChatHistory()
    chat_history.add_user_message("User message")
    assert filter_system_message(chat_history) is None

    # Test with multiple system messages
    chat_history = ChatHistory()
    chat_history.add_system_message("System message 1")
    chat_history.add_system_message("System message 2")
    with pytest.raises(ServiceInvalidRequestError):
        filter_system_message(chat_history)
