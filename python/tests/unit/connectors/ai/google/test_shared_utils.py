# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.google.shared_utils import (
    FUNCTION_CHOICE_TYPE_TO_GOOGLE_FUNCTION_CALLING_MODE,
    GEMINI_FUNCTION_NAME_SEPARATOR,
    collapse_function_call_results_in_chat_history,
    filter_system_message,
    format_gemini_function_name_to_kernel_function_fully_qualified_name,
    sanitize_schema_for_google_ai,
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


# --- sanitize_schema_for_google_ai tests ---


def test_sanitize_schema_none():
    """Test that None input returns None."""
    assert sanitize_schema_for_google_ai(None) is None


def test_sanitize_schema_simple_passthrough():
    """Test that a simple schema passes through unchanged."""
    schema = {"type": "string", "description": "A name"}
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string", "description": "A name"}


def test_sanitize_schema_type_as_list_with_null():
    """type: ["string", "null"] should become type: "string" + nullable: true."""
    schema = {"type": ["string", "null"], "description": "Optional field"}
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string", "nullable": True, "description": "Optional field"}


def test_sanitize_schema_type_as_list_without_null():
    """type: ["string", "integer"] should pick the first type."""
    schema = {"type": ["string", "integer"]}
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string"}


def test_sanitize_schema_anyof_with_null():
    """AnyOf with null variant should become the non-null type + nullable."""
    schema = {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "description": "Optional param",
    }
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string", "nullable": True, "description": "Optional param"}


def test_sanitize_schema_anyof_without_null():
    """AnyOf without null should pick the first variant."""
    schema = {
        "anyOf": [
            {"type": "string"},
            {"type": "array", "items": {"type": "string"}},
        ],
    }
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string"}


def test_sanitize_schema_oneof():
    """OneOf should be handled the same as anyOf."""
    schema = {
        "oneOf": [{"type": "integer"}, {"type": "null"}],
    }
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "integer", "nullable": True}


def test_sanitize_schema_nested_properties():
    """AnyOf inside nested properties should be sanitized recursively."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"anyOf": [{"type": "number"}, {"type": "null"}]},
        },
    }
    result = sanitize_schema_for_google_ai(schema)
    assert result == {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number", "nullable": True},
        },
    }


def test_sanitize_schema_nested_items():
    """AnyOf inside array items should be sanitized recursively."""
    schema = {
        "type": "array",
        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
    }
    result = sanitize_schema_for_google_ai(schema)
    assert result == {
        "type": "array",
        "items": {"type": "string"},
    }


def test_sanitize_schema_does_not_mutate_original():
    """The original schema dict should not be modified."""
    schema = {
        "anyOf": [{"type": "string"}, {"type": "null"}],
        "description": "test",
    }
    original = {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "test"}
    sanitize_schema_for_google_ai(schema)
    assert schema == original


def test_sanitize_schema_agent_messages_param():
    """Reproducer for issue #12442: str | list[str] parameter schema."""
    schema = {
        "anyOf": [
            {"type": "string"},
            {"type": "array", "items": {"type": "string"}},
        ],
        "description": "The user messages for the agent.",
    }
    result = sanitize_schema_for_google_ai(schema)
    assert "anyOf" not in result
    assert result["type"] == "string"
    assert result["description"] == "The user messages for the agent."


def test_sanitize_schema_allof():
    """AllOf should be handled like anyOf/oneOf, picking the first variant."""
    schema = {
        "allOf": [
            {"type": "object", "properties": {"name": {"type": "string"}}},
            {"type": "object", "properties": {"age": {"type": "integer"}}},
        ],
    }
    result = sanitize_schema_for_google_ai(schema)
    assert "allOf" not in result
    assert result["type"] == "object"
    assert "name" in result["properties"]


def test_sanitize_schema_allof_with_null():
    """AllOf with a null variant should produce nullable: true."""
    schema = {
        "allOf": [{"type": "string"}, {"type": "null"}],
    }
    result = sanitize_schema_for_google_ai(schema)
    assert "allOf" not in result
    assert result["type"] == "string"
    assert result["nullable"] is True


def test_sanitize_schema_all_null_type_list():
    """type: ["null"] should fall back to type: "string" + nullable: true."""
    schema = {"type": ["null"]}
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string", "nullable": True}


def test_sanitize_schema_all_null_anyof():
    """AnyOf where all variants are null should fall back to type: "string"."""
    schema = {"anyOf": [{"type": "null"}]}
    result = sanitize_schema_for_google_ai(schema)
    assert result == {"type": "string", "nullable": True}


def test_sanitize_schema_chosen_variant_keeps_own_description():
    """When the chosen anyOf variant has its own description, do not overwrite it."""
    schema = {
        "anyOf": [
            {"type": "string", "description": "inner desc"},
            {"type": "null"},
        ],
        "description": "outer desc",
    }
    result = sanitize_schema_for_google_ai(schema)
    assert result["description"] == "inner desc"
    assert result["nullable"] is True
