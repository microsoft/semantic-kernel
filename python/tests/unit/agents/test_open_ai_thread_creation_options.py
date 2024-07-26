# Copyright (c) Microsoft. All rights reserved.


import pytest
from pydantic import ValidationError

from semantic_kernel.agents.open_ai.open_ai_thread_creation_options import OpenAIThreadCreationOptions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


def test_default_values():
    options = OpenAIThreadCreationOptions()
    assert options.code_interpreter_file_ids == []
    assert options.messages == []
    assert options.vector_store_id is None
    assert options.metadata == {}


def test_code_interpreter_file_ids_max_length():
    options = OpenAIThreadCreationOptions(code_interpreter_file_ids=["file1"] * 64)
    assert len(options.code_interpreter_file_ids) == 64

    with pytest.raises(ValidationError):
        OpenAIThreadCreationOptions(code_interpreter_file_ids=["file1"] * 65)


def test_messages_field():
    messages = [
        ChatMessageContent(role=AuthorRole.USER, content="Hello"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="World"),
    ]
    options = OpenAIThreadCreationOptions(messages=messages)
    assert len(options.messages) == 2
    assert options.messages[0].content == "Hello"
    assert options.messages[0].role == AuthorRole.USER
    assert options.messages[1].content == "World"
    assert options.messages[1].role == AuthorRole.ASSISTANT


def test_vector_store_id_field():
    options = OpenAIThreadCreationOptions(vector_store_id="vector_store")
    assert options.vector_store_id == "vector_store"


def test_metadata_field():
    metadata = {"key1": "value1", "key2": "value2"}
    options = OpenAIThreadCreationOptions(metadata=metadata)
    assert options.metadata == metadata


def test_empty_metadata():
    options = OpenAIThreadCreationOptions(metadata={})
    assert options.metadata == {}


def test_metadata_with_empty_values():
    metadata = {"key1": "", "key2": ""}
    options = OpenAIThreadCreationOptions(metadata=metadata)
    assert options.metadata == metadata
