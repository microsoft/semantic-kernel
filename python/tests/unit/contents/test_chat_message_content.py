# Copyright (c) Microsoft. All rights reserved.

import pytest
from defusedxml.ElementTree import XML

from semantic_kernel.contents.author_role import AuthorRole
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent


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
        items=[
            TextContent(text="Hello, world!"),
            TextContent(text="Hello, world!"),
        ],
    )
    assert message.role == AuthorRole.SYSTEM
    assert message.content == "Hello, world!"
    assert len(message.items) == 2


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
    message = ChatMessageContent(role=AuthorRole.USER, content="Hello, world!", name=None)
    element = message.to_element()
    assert element.tag == "message"
    assert element.attrib == {"role": "user"}
    assert element.get("name") is None
    for child in element:
        assert child.tag == "text"
        assert child.text == "Hello, world!"


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
    ],
    ids=["user_content", "user_with_name", "user_item", "function_call", "function_result", "multiple_items"],
)
def test_cmc_to_dict_items(input_args, expected_dict):
    message = ChatMessageContent(**input_args)
    assert message.to_dict() == expected_dict
