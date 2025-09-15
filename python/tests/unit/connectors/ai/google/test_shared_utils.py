# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.google.shared_utils import (
    FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE,
    GEMINI_FUNCTION_NAME_SEPARATOR,
    collapse_function_call_results_in_chat_history,
    filter_system_message,
    format_gemini_function_name_to_kernel_function_fully_qualified_name,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
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


def test_function_choice_type_to_google_function_calling_mode_contain_all_types() -> None:
    assert FunctionChoiceType.AUTO in FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE
    assert FunctionChoiceType.NONE in FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE
    assert FunctionChoiceType.REQUIRED in FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE


def test_format_gemini_function_name_to_kernel_function_fully_qualified_name() -> None:
    # Contains the separator
    gemini_function_name = f"plugin{GEMINI_FUNCTION_NAME_SEPARATOR}function"
    assert (
        format_gemini_function_name_to_kernel_function_fully_qualified_name(gemini_function_name) == "plugin-function"
    )

    # Doesn't contain the separator
    gemini_function_name = "function"
    assert format_gemini_function_name_to_kernel_function_fully_qualified_name(gemini_function_name) == "function"


def test_collapse_function_call_results_in_chat_history() -> None:
    chat_history = ChatHistory()
    chat_history.extend([
        ChatMessageContent(
            AuthorRole.ASSISTANT,
            items=[
                FunctionCallContent(id="function1", name="function1"),
                FunctionCallContent(id="function2", name="function2"),
            ],
        ),
        # The following two messages should be collapsed into a single message
        ChatMessageContent(
            AuthorRole.TOOL,
            items=[FunctionResultContent(id="function1", name="function1", result="result1")],
        ),
        ChatMessageContent(
            AuthorRole.TOOL,
            items=[FunctionResultContent(id="function2", name="function2", result="result2")],
        ),
        ChatMessageContent(AuthorRole.ASSISTANT, content="Assistant message"),
        ChatMessageContent(AuthorRole.USER, content="User message"),
        ChatMessageContent(
            AuthorRole.ASSISTANT,
            items=[FunctionCallContent(id="function3", name="function3")],
        ),
        ChatMessageContent(
            AuthorRole.TOOL,
            items=[FunctionResultContent(id="function3", name="function3", result="result3")],
        ),
        ChatMessageContent(AuthorRole.ASSISTANT, content="Assistant message"),
    ])

    assert len(chat_history.messages) == 8
    collapse_function_call_results_in_chat_history(chat_history)
    assert len(chat_history.messages) == 7
    assert len(chat_history.messages[1].items) == 2
