# Copyright (c) Microsoft. All rights reserved.

import pytest
from defusedxml.ElementTree import XML

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason


def test_cmc():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_cmc_str():
    message = ChatMessageContent(role="user", content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert str(message) == "Hello, world!"


def test_cmc_full():
    message = ChatMessageContent(
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


def test_cmc_items():
    message = ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text="Hello, world!")])
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_cmc_items_and_content():
    message = ChatMessageContent(role=AuthorRole.USER, content="text", items=[TextContent(text="Hello, world!")])
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert message.items[0].text == "Hello, world!"
    assert message.items[1].text == "text"
    assert len(message.items) == 2


def test_cmc_multiple_items():
    message = ChatMessageContent(
        role=AuthorRole.SYSTEM,
        items=[TextContent(text="Hello, world!"), TextContent(text="Hello, world!"), ImageContent(uri="http://test/")],
    )
    assert message.role == AuthorRole.SYSTEM
    assert message.content == "Hello, world!"
    assert len(message.items) == 3


def test_cmc_content_set():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    message.content = "Hello, world to you too!"
    assert len(message.items) == 1
    assert message.items[0].text == "Hello, world to you too!"
    message.content = ""
    assert message.items[0].text == "Hello, world to you too!"


def test_cmc_content_set_empty():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    message.items.pop()
    message.content = "Hello, world to you too!"
    assert len(message.items) == 1
    assert message.items[0].text == "Hello, world to you too!"


def test_cmc_to_element():
    message = ChatMessageContent(
        role=AuthorRole.USER, items=[TextContent(text="Hello, world!", encoding="utf8")], name=None
    )
    element = message.to_element()
    assert element.tag == "message"
    assert element.attrib == {"role": "user"}
    assert element.get("name") is None
    for child in element:
        assert child.tag == "text"
        assert child.text == "Hello, world!"


@pytest.mark.parametrize(
    "message",
    [
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="test"),
            ],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[ImageContent(uri="http://test/")],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[ImageContent(data=b"test_data", mime_type="image/jpeg")],
        ),
        ChatMessageContent(
            role=AuthorRole.USER, items=[FunctionCallContent(id="test", name="func_name", arguments="args")]
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[FunctionResultContent(id="test", name="func_name", result="result")],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Hello, world!"),
                FunctionCallContent(id="test", name="func_name", arguments="args"),
                FunctionResultContent(id="test", name="func_name", result="result"),
                ImageContent(uri="http://test/"),
            ],
        ),
    ],
    ids=["text", "image_uri", "image_data", "function_call", "function_result", "all"],
)
def test_cmc_to_from_element(message):
    element = message.to_element()
    new_message = ChatMessageContent.from_element(element)
    assert message == new_message


def test_cmc_to_prompt():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
    prompt = message.to_prompt()
    assert prompt == '<message role="user"><text>Hello, world!</text></message>'


def test_cmc_from_element():
    element = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!").to_element()
    message = ChatMessageContent.from_element(element)
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_cmc_from_element_content():
    xml_content = '<message role="user">Hello, world!</message>'
    element = XML(text=xml_content)
    message = ChatMessageContent.from_element(element)
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


@pytest.mark.parametrize(
    "xml_content, user, text_content, length",
    [
        ('<message role="user">Hello, world!</message>', "user", "Hello, world!", 1),
        ('<message role="user"><text>Hello, world!</text></message>', "user", "Hello, world!", 1),
        (
            '<message role="user"><text>Hello, world!</text><text>Hello, world!</text></message>',
            "user",
            "Hello, world!Hello, world!",
            1,
        ),
        (
            '<message role="assistant"><function_call id="test" name="func_name">args</function_call></message>',
            "assistant",
            "",
            1,
        ),
        (
            '<message role="tool"><function_result id="test" name="func_name">function result</function_result></message>',  # noqa: E501
            "tool",
            "",
            1,
        ),
        (
            '<message role="user"><text>Hello, world!</text><function_call id="test" name="func_name">args</function_call></message>',  # noqa: E501
            "user",
            "Hello, world!",
            2,
        ),
        (
            '<message role="user"><random>some random code sample</random>in between text<text>test</text></message>',
            "user",
            "<random>some random code sample</random>in between texttest",
            1,  # TODO: review this case
        ),
        ('<message role="user" choice_index="0">Hello, world!</message>', "user", "Hello, world!", 1),
        ('<message role="user"><image>data:image/jpeg;base64,dGVzdF9kYXRh</image></message>', "user", "", 1),
    ],
    ids=[
        "no_tag",
        "text_tag",
        "double_text_tag",
        "function_call",
        "function_result",
        "combined",
        "unknown_tag",
        "streaming",
        "image",
    ],
)
def test_cmc_from_element_content_parse(xml_content, user, text_content, length):
    element = XML(text=xml_content)
    message = ChatMessageContent.from_element(element)
    assert message.role.value == user
    assert str(message) == text_content
    assert len(message.items) == length


def test_cmc_serialize():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
    dumped = message.model_dump()
    assert dumped["role"] == AuthorRole.USER
    assert dumped["items"][0]["text"] == "Hello, world!"


def test_cmc_to_dict():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
    assert message.to_dict() == {
        "role": "user",
        "content": "Hello, world!",
    }


def test_cmc_to_dict_keys():
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!")
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
        (
            {
                "role": "user",
                "items": [
                    {"content_type": "text", "text": "Hello, "},
                    {"content_type": "text", "text": "world!"},
                ],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": "Hello, "}, {"type": "text", "text": "world!"}],
            },
        ),
        (
            {
                "role": "user",
                "items": [
                    {"content_type": "annotation", "file_id": "test"},
                ],
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": "type=None, test None (Start Index=None->End Index=None)"}],
            },
        ),
        (
            {
                "role": "user",
                "items": [
                    {"content_type": "file_reference", "file_id": "test"},
                ],
            },
            {
                "role": "user",
                "content": [{"file_id": "test"}],
            },
        ),
        (
            {
                "role": "user",
                "items": [
                    {"content_type": "function_call", "name": "test-test"},
                ],
            },
            {
                "role": "user",
                "content": [{"id": None, "type": "function", "function": {"name": "test-test", "arguments": None}}],
            },
        ),
        (
            {
                "role": "user",
                "items": [
                    {"content_type": "function_call", "name": "test-test"},
                    {"content_type": "function_result", "name": "test-test", "result": "test", "id": "test"},
                ],
            },
            {
                "role": "user",
                "content": [
                    {"id": None, "type": "function", "function": {"name": "test-test", "arguments": None}},
                    {"tool_call_id": "test", "content": "test"},
                ],
            },
        ),
        (
            {
                "role": "user",
                "items": [
                    {"content_type": "image", "uri": "http://test"},
                ],
            },
            {
                "role": "user",
                "content": [{"image_url": {"url": "http://test/"}, "type": "image_url"}],
            },
        ),
    ],
    ids=[
        "user_content",
        "user_with_name",
        "user_item",
        "function_call",
        "function_result",
        "multiple_items",
        "multiple_items_serialize",
        "annotations_serialize",
        "file_reference_serialize",
        "function_call_serialize",
        "function_result_serialize",
        "image_serialize",
    ],
)
def test_cmc_to_dict_items(input_args, expected_dict):
    message = ChatMessageContent(**input_args)
    assert message.to_dict() == expected_dict


def test_cmc_with_unhashable_types_can_hash():
    user_messages = [
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Describe this image."),
                ImageContent(
                    uri="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg"
                ),
            ],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="What is the main color in this image?"),
                ImageContent(uri="https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"),
            ],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Is there an animal in this image?"),
                FileReferenceContent(file_id="test_file_id"),
            ],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
        ),
    ]

    for message in user_messages:
        assert hash(message) is not None
