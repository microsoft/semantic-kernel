# Copyright (c) Microsoft. All rights reserved.

import pytest
from defusedxml.ElementTree import XML

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.content_exceptions import ContentAdditionException


def test_scmc():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_scmc_str():
    message = StreamingChatMessageContent(choice_index=0, role="user", content="Hello, world!")
    assert str(message) == "Hello, world!"


def test_scmc_full():
    message = StreamingChatMessageContent(
        choice_index=0,
        role=AuthorRole.USER,
        name="username",
        content="Hello, world!",
        inner_content="Hello, world!",
        encoding="utf-8",
        ai_model_id="1234",
        metadata={"test": "test"},
        finish_reason="stop",
    )
    assert message.role == AuthorRole.USER
    assert message.name == "username"
    assert message.content == "Hello, world!"
    assert message.finish_reason == FinishReason.STOP
    assert len(message.items) == 1


def test_scmc_items():
    message = StreamingChatMessageContent(
        choice_index=0, role=AuthorRole.USER, items=[TextContent(text="Hello, world!")]
    )
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_scmc_items_and_content():
    message = StreamingChatMessageContent(
        choice_index=0, role=AuthorRole.USER, content="text", items=[TextContent(text="Hello, world!")]
    )
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert message.items[0].text == "Hello, world!"
    assert message.items[1].text == "text"
    assert len(message.items) == 2


def test_scmc_multiple_items():
    message = StreamingChatMessageContent(
        choice_index=0,
        role=AuthorRole.SYSTEM,
        items=[
            TextContent(text="Hello, world!"),
            TextContent(text="Hello, world!"),
        ],
    )
    assert message.role == AuthorRole.SYSTEM
    assert message.content == "Hello, world!"
    assert len(message.items) == 2


def test_scmc_content_set():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    message.content = "Hello, world to you too!"
    assert len(message.items) == 1
    assert message.items[0].text == "Hello, world to you too!"
    message.content = ""
    assert message.items[0].text == "Hello, world to you too!"


def test_scmc_content_set_empty():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    message.items.pop()
    message.content = "Hello, world to you too!"
    assert len(message.items) == 1
    assert message.items[0].text == "Hello, world to you too!"


def test_scmc_to_element():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!", name=None)
    element = message.to_element()
    assert element.tag == "message"
    assert element.attrib == {"role": "user", "choice_index": "0"}
    assert element.get("name") is None
    for child in element:
        assert child.tag == "text"
        assert child.text == "Hello, world!"


def test_scmc_to_prompt():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    prompt = message.to_prompt()
    assert "<text>Hello, world!</text>" in prompt
    assert 'choice_index="0"' in prompt
    assert 'role="user"' in prompt


def test_scmc_from_element():
    element = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!").to_element()
    message = StreamingChatMessageContent.from_element(element)
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_scmc_from_element_content():
    xml_content = '<message role="user" choice_index="0">Hello, world!</message>'
    element = XML(text=xml_content)
    message = StreamingChatMessageContent.from_element(element)
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_scmc_from_element_content_missing_choice_index():
    xml_content = '<message role="user">Hello, world!</message>'
    element = XML(text=xml_content)
    with pytest.raises(TypeError):
        StreamingChatMessageContent.from_element(element)


@pytest.mark.parametrize(
    "xml_content, user, text_content, length",
    [
        ('<message role="user" choice_index="0">Hello, world!</message>', "user", "Hello, world!", 1),
        ('<message role="user" choice_index="0"><text>Hello, world!</text></message>', "user", "Hello, world!", 1),
        (
            '<message role="user" choice_index="0"><text>Hello, world!</text><text>Hello, world!</text></message>',
            "user",
            "Hello, world!Hello, world!",
            1,
        ),
        (
            '<message role="assistant" choice_index="0"><function_call id="test" name="func_name">args</function_call></message>',  # noqa: E501
            "assistant",
            "",
            1,
        ),
        (
            '<message role="tool" choice_index="0"><function_result id="test" name="func_name">function result</function_result></message>',  # noqa: E501
            "tool",
            "",
            1,
        ),
        (
            '<message role="user" choice_index="0"><text>Hello, world!</text><function_call id="test" name="func_name">args</function_call></message>',  # noqa: E501
            "user",
            "Hello, world!",
            2,
        ),
        (
            '<message role="user" choice_index="0"><random>some random code sample</random>in between text<text>test</text></message>',  # noqa: E501
            "user",
            "<random>some random code sample</random>in between texttest",
            1,  # TODO: review this case
        ),
    ],
    ids=["no_tag", "text_tag", "double_text_tag", "function_call", "function_result", "combined", "unknown_tag"],
)
def test_scmc_from_element_content_parse(xml_content, user, text_content, length):
    element = XML(text=xml_content)
    message = StreamingChatMessageContent.from_element(element)
    assert message.role.value == user
    assert str(message) == text_content
    assert len(message.items) == length


def test_scmc_serialize():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    dumped = message.model_dump()
    assert dumped["role"] == AuthorRole.USER
    assert dumped["items"][0]["text"] == "Hello, world!"


def test_scmc_to_dict():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    assert message.to_dict() == {
        "role": "user",
        "content": "Hello, world!",
    }


def test_scmc_to_dict_keys():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    assert message.to_dict(role_key="author", content_key="text") == {
        "author": "user",
        "text": "Hello, world!",
    }


@pytest.mark.parametrize(
    "input_args, expected_dict",
    [
        ({"role": "user", "content": "Hello, world!"}, {"role": "user", "content": "Hello, world!"}),
        (
            {"role": "user", "content": "Hello, world!", "name": "username"},
            {"role": "user", "content": "Hello, world!", "name": "username"},
        ),
        ({"role": "user", "items": [TextContent(text="Hello, world!")]}, {"role": "user", "content": "Hello, world!"}),
        (
            {"role": "assistant", "items": [FunctionCallContent(id="test", name="func_name", arguments="args")]},
            {
                "role": "assistant",
                "tool_calls": [
                    {"id": "test", "type": "function", "function": {"name": "func_name", "arguments": "args"}}
                ],
            },
        ),
        (
            {"role": "tool", "items": [FunctionResultContent(id="test", name="func_name", result="result")]},
            {"role": "tool", "tool_call_id": "test", "content": "result"},
        ),
        (
            {
                "role": "user",
                "items": [
                    TextContent(text="Hello, "),
                    TextContent(text="world!"),
                ],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": "Hello, "}, {"type": "text", "text": "world!"}],
            },
        ),
    ],
    ids=["user_content", "user_with_name", "user_item", "function_call", "function_result", "multiple_items"],
)
def test_scmc_to_dict_items(input_args, expected_dict):
    message = StreamingChatMessageContent(choice_index=0, **input_args)
    assert message.to_dict() == expected_dict


def test_scmc_add():
    message1 = StreamingChatMessageContent(
        choice_index=0, role=AuthorRole.USER, content="Hello, ", inner_content="source1"
    )
    message2 = StreamingChatMessageContent(
        choice_index=0, role=AuthorRole.USER, content="world!", inner_content="source2"
    )
    combined = message1 + message2
    assert combined.role == AuthorRole.USER
    assert combined.content == "Hello, world!"
    assert len(combined.items) == 1
    assert len(combined.inner_content) == 2

    # Make sure the original inner content is preserved
    assert message1.inner_content == "source1"
    assert message2.inner_content == "source2"


def test_scmc_add_three():
    message1 = StreamingChatMessageContent(
        choice_index=0, role=AuthorRole.USER, content="Hello, ", inner_content="source1"
    )
    message2 = StreamingChatMessageContent(
        choice_index=0, role=AuthorRole.USER, content="world", inner_content="source2"
    )
    message3 = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="!", inner_content="source3")
    combined = message1 + message2 + message3
    assert combined.role == AuthorRole.USER
    assert combined.content == "Hello, world!"
    assert len(combined.items) == 1
    assert len(combined.inner_content) == 3


@pytest.mark.parametrize(
    "message1, message2",
    [
        (
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.USER,
                items=[StreamingTextContent(choice_index=0, text="Hello, ")],
                inner_content="source1",
            ),
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.USER,
                items=[FunctionResultContent(id="test", name="test", result="test")],
                inner_content="source2",
            ),
        ),
        (
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.TOOL,
                items=[FunctionCallContent(id="test1", name="test")],
                inner_content="source1",
            ),
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.TOOL,
                items=[FunctionCallContent(id="test2", name="test")],
                inner_content="source2",
            ),
        ),
        (
            StreamingChatMessageContent(
                choice_index=0, role=AuthorRole.USER, items=[StreamingTextContent(text="Hello, ", choice_index=0)]
            ),
            StreamingChatMessageContent(
                choice_index=0, role=AuthorRole.USER, items=[StreamingTextContent(text="world!", choice_index=1)]
            ),
        ),
        (
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.USER,
                items=[StreamingTextContent(text="Hello, ", choice_index=0, ai_model_id="0")],
            ),
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.USER,
                items=[StreamingTextContent(text="world!", choice_index=0, ai_model_id="1")],
            ),
        ),
        (
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.USER,
                items=[StreamingTextContent(text="Hello, ", encoding="utf-8", choice_index=0)],
            ),
            StreamingChatMessageContent(
                choice_index=0,
                role=AuthorRole.USER,
                items=[StreamingTextContent(text="world!", encoding="utf-16", choice_index=0)],
            ),
        ),
    ],
    ids=[
        "different_types",
        "different_fccs",
        "different_text_content_choice_index",
        "different_text_content_models",
        "different_text_content_encoding",
    ],
)
def test_scmc_add_different_items_same_type(message1, message2):
    combined = message1 + message2
    assert len(combined.items) == 2

    # Make sure the original items are preserved
    assert len(message1.items) == 1
    assert len(message2.items) == 1


@pytest.mark.parametrize(
    "message1, message2",
    [
        (
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, "),
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.ASSISTANT, content="world!"),
        ),
        (
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, "),
            StreamingChatMessageContent(choice_index=1, role=AuthorRole.USER, content="world!"),
        ),
        (
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, ", ai_model_id="1234"),
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="world!", ai_model_id="5678"),
        ),
        (
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, ", encoding="utf-8"),
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="world!", encoding="utf-16"),
        ),
        (
            StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, "),
            ChatMessageContent(role=AuthorRole.USER, content="world!"),
        ),
    ],
    ids=[
        "different_roles",
        "different_index",
        "different_model",
        "different_encoding",
        "different_type",
    ],
)
def test_smsc_add_exception(message1, message2):
    with pytest.raises(ContentAdditionException):
        message1 + message2


def test_scmc_bytes():
    message = StreamingChatMessageContent(choice_index=0, role=AuthorRole.USER, content="Hello, world!")
    assert bytes(message) == b"Hello, world!"
    assert bytes(message.items[0]) == b"Hello, world!"


def test_scmc_with_unhashable_types_can_hash():
    user_messages = [
        StreamingChatMessageContent(
            role=AuthorRole.USER,
            items=[
                StreamingTextContent(text="Describe this image.", choice_index=0),
                ImageContent(
                    uri="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg"
                ),
            ],
            choice_index=0,
        ),
        StreamingChatMessageContent(
            role=AuthorRole.USER,
            items=[
                StreamingTextContent(text="What is the main color in this image?", choice_index=0),
                ImageContent(uri="https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"),
            ],
            choice_index=0,
        ),
        StreamingChatMessageContent(
            role=AuthorRole.USER,
            items=[
                StreamingTextContent(text="Is there an animal in this image?", choice_index=0),
                FileReferenceContent(file_id="test_file_id"),
            ],
            choice_index=0,
        ),
        StreamingChatMessageContent(
            role=AuthorRole.USER,
            choice_index=0,
        ),
    ]

    for message in user_messages:
        assert hash(message) is not None
