# Copyright (c) Microsoft. All rights reserved.

import pytest
from defusedxml.ElementTree import XML

from semantic_kernel.contents.author_role import AuthorRole
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.text_content import TextContent


def test_cmc_empty():
    with pytest.raises(ValueError):
        ChatMessageContent(role="user")


def test_cmc():
    message = ChatMessageContent(role="user", content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_cmc_str():
    message = ChatMessageContent(role="user", content="Hello, world!")
    assert str(message) == "Hello, world!"


def test_cmc_full():
    message = ChatMessageContent(
        role="user",
        content="Hello, world!",
        inner_content="Hello, world!",
        encoding="utf-8",
        ai_model_id="1234",
        metadata={"test": "test"},
        finish_reason="stop",
    )
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert message.finish_reason == FinishReason.STOP
    assert len(message.items) == 1


def test_cmc_items():
    message = ChatMessageContent(role="user", items=[TextContent(text="Hello, world!")])
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    assert len(message.items) == 1


def test_cmc_multiple_items():
    message = ChatMessageContent(
        role="system",
        items=[
            TextContent(text="Hello, world!"),
            TextContent(text="Hello, world!"),
        ],
    )
    assert message.role == AuthorRole.SYSTEM
    assert message.content == "Hello, world!"
    assert len(message.items) == 2


def test_cmc_content_set():
    message = ChatMessageContent(role="user", content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    message.content = "Hello, world to you too!"
    assert len(message.items) == 1
    assert message.items[0].text == "Hello, world to you too!"


def test_cmc_content_set_empty():
    message = ChatMessageContent(role="user", content="Hello, world!")
    assert message.role == AuthorRole.USER
    assert message.content == "Hello, world!"
    message.items.pop()
    message.content = "Hello, world to you too!"
    assert len(message.items) == 1
    assert message.items[0].text == "Hello, world to you too!"


def test_cmc_to_element():
    message = ChatMessageContent(role="user", content="Hello, world!")
    element = message.to_element("message")
    assert element.tag == "message"
    assert element.attrib == {"role": "user"}
    for child in element:
        assert child.tag == "text"
        assert child.text == "Hello, world!"


def test_cmc_to_prompt():
    message = ChatMessageContent(role="user", content="Hello, world!")
    prompt = message.to_prompt("message")
    assert prompt == '<message role="user"><text>Hello, world!</text></message>'


def test_cmc_from_element():
    element = ChatMessageContent(role="user", content="Hello, world!").to_element("message")
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


def test_cmc_serialize():
    message = ChatMessageContent(role="user", content="Hello, world!")
    dumped = message.model_dump()
    assert dumped["role"] == "user"
    assert dumped["items"][0]["text"] == "Hello, world!"
