# Copyright (c) Microsoft. All rights reserved.


import pytest

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ContentInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.input_variable import InputVariable
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent
from semantic_kernel.connectors.ai.open_ai.models.chat_completion.function_call import FunctionCall
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_init_with_system_message_only():
    system_msg = "test message"
    chat_history = ChatHistory(system_message=system_msg)
    assert len(chat_history.messages) == 1
    assert chat_history.messages[0].content == system_msg


def test_init_with_messages_only():
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    msgs = [
        ChatMessageContent(role=AuthorRole.USER, content=f"Message {i}")
        for i in range(3)
    ]
    chat_history = ChatHistory(messages=msgs)
    assert (
        chat_history.messages == msgs
    ), "Chat history should contain exactly the provided messages"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
=======
>>>>>>> Stashed changes
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
    chat_history = ChatHistory(messages=msgs)
    assert chat_history.messages == msgs, "Chat history should contain exactly the provided messages"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


def test_init_with_messages_and_system_message():
    system_msg = "a test system prompt"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    msgs = [
        ChatMessageContent(role=AuthorRole.USER, content=f"Message {i}")
        for i in range(3)
    ]
    chat_history = ChatHistory(messages=msgs, system_message=system_msg)
    assert (
        chat_history.messages[0].role == AuthorRole.SYSTEM
    ), "System message should be the first in history"
    assert (
        chat_history.messages[0].content == system_msg
    ), "System message should be the first in history"
    assert (
        chat_history.messages[1:] == msgs
    ), "Remaining messages should follow the system message"


def test_init_without_messages_and_system_message(chat_history: ChatHistory):
    assert (
        chat_history.messages == []
    ), "Chat history should be empty if no messages and system_message are provided"


def test_add_system_message(chat_history: ChatHistory):
    content = "System message"
    chat_history.add_system_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == AuthorRole.SYSTEM


def test_add_system_message_item(chat_history: ChatHistory):
    content = [TextContent(text="System message")]
    chat_history.add_system_message(content)
    assert chat_history.messages[-1].content == str(content[0])
    assert chat_history.messages[-1].role == AuthorRole.SYSTEM


def test_add_system_message_at_init():
    content = "System message"
    chat_history = ChatHistory(system_message=content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == AuthorRole.SYSTEM


def test_add_user_message(chat_history: ChatHistory):
    content = "User message"
    chat_history.add_user_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == AuthorRole.USER


def test_add_user_message_list(chat_history: ChatHistory):
    content = [TextContent(text="User message")]
    chat_history.add_user_message(content)
    assert chat_history.messages[-1].content == content[0].text
    assert chat_history.messages[-1].role == AuthorRole.USER


def test_add_assistant_message(chat_history: ChatHistory):
    content = "Assistant message"
    chat_history.add_assistant_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == AuthorRole.ASSISTANT


def test_add_assistant_message_list(chat_history: ChatHistory):
    content = [TextContent(text="Assistant message")]
    chat_history.add_assistant_message(content)
    assert chat_history.messages[-1].content == content[0].text
    assert chat_history.messages[-1].role == AuthorRole.ASSISTANT


def test_add_tool_message(chat_history: ChatHistory):
    content = "Tool message"
    chat_history.add_tool_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == AuthorRole.TOOL


def test_add_tool_message_list(chat_history: ChatHistory):
    content = [FunctionResultContent(id="test", result="Tool message")]
    chat_history.add_tool_message(content)
    assert chat_history.messages[-1].items[0].result == content[0].result
    assert chat_history.messages[-1].role == AuthorRole.TOOL


def test_add_message(chat_history: ChatHistory):
    content = "Test message"
    role = AuthorRole.USER
    encoding = "utf-8"
    chat_history.add_message(
        message={"role": role, "content": content},
        encoding=encoding,
        metadata={"test": "test"},
    )
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == role
    assert chat_history.messages[-1].encoding == encoding
    assert chat_history.messages[-1].metadata == {"test": "test"}


def test_add_message_with_image(chat_history: ChatHistory):
    content = "Test message"
    role = AuthorRole.USER
    encoding = "utf-8"
    chat_history.add_message(
        ChatMessageContent(
            role=role,
            items=[
                TextContent(text=content),
                ImageContent(uri="https://test/"),
            ],
            encoding=encoding,
        )
    )
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == role
    assert chat_history.messages[-1].encoding == encoding
    if str(chat_history.messages[-1].items[1].uri) != "https://test/": raise AssertionError("URI does not match expected value")


def test_add_message_invalid_message(chat_history: ChatHistory):
    content = "Test message"
    with pytest.raises(ContentInitializationError):
        chat_history.add_message(message={"content": content})


def test_add_message_invalid_type(chat_history: ChatHistory):
    content = "Test message"
    with pytest.raises(ContentInitializationError):
        chat_history.add_message(message=content)


def test_remove_message(chat_history: ChatHistory):
    content = "Message to remove"
    role = AuthorRole.USER
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
    chat_history = ChatHistory(messages=msgs, system_message=system_msg)
    assert chat_history.messages[0].role == ChatRole.SYSTEM, "System message should be the first in history"
    assert chat_history.messages[0].content == system_msg, "System message should be the first in history"
    assert chat_history.messages[1:] == msgs, "Remaining messages should follow the system message"


def test_init_without_messages_and_system_message():
    chat_history = ChatHistory()
    assert chat_history.messages == [], "Chat history should be empty if no messages and system_message are provided"


def test_add_system_message():
    chat_history = ChatHistory()
    content = "System message"
    chat_history.add_system_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.SYSTEM


def test_add_system_message_at_init():
    chat_history = ChatHistory()
    content = "System message"
    chat_history = ChatHistory(system_message=content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.SYSTEM


def test_add_user_message():
    chat_history = ChatHistory()
    content = "User message"
    chat_history.add_user_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.USER


def test_add_assistant_message():
    chat_history = ChatHistory()
    content = "Assistant message"
    chat_history.add_assistant_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.ASSISTANT


def test_add_tool_message():
    chat_history = ChatHistory()
    content = "Tool message"
    chat_history.add_tool_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.TOOL


def test_add_message():
    chat_history = ChatHistory()
    content = "Test message"
    role = ChatRole.USER
    encoding = "utf-8"
    chat_history.add_message(message={"role": role, "content": content}, encoding=encoding)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == role
    assert chat_history.messages[-1].encoding == encoding


def test_add_message_invalid_message():
    chat_history = ChatHistory()
    content = "Test message"
    with pytest.raises(ValueError):
        chat_history.add_message(message={"content": content})


def test_add_message_invalid_type():
    chat_history = ChatHistory()
    content = "Test message"
    with pytest.raises(ValueError):
        chat_history.add_message(message=content)


def test_remove_message():
    chat_history = ChatHistory()
    content = "Message to remove"
    role = ChatRole.USER
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert chat_history.remove_message(message) is True
    assert message not in chat_history.messages


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_remove_message_invalid(chat_history: ChatHistory):
    content = "Message to remove"
    role = AuthorRole.USER
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def test_remove_message_invalid(chat_history: ChatHistory):
    content = "Message to remove"
    role = AuthorRole.USER
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
def test_remove_message_invalid(chat_history: ChatHistory):
    content = "Message to remove"
    role = AuthorRole.USER
=======
def test_remove_message_invalid():
    chat_history = ChatHistory()
    content = "Message to remove"
    role = ChatRole.USER
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert chat_history.remove_message("random") is False


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_len(chat_history: ChatHistory):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
def test_len(chat_history: ChatHistory):
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
def test_len(chat_history: ChatHistory):
=======
>>>>>>> Stashed changes
=======
def test_len(chat_history: ChatHistory):
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
def test_len(chat_history: ChatHistory):
=======
def test_len():
    chat_history = ChatHistory()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    content = "Message"
    chat_history.add_user_message(content)
    chat_history.add_system_message(content)
    assert len(chat_history) == 2


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_getitem(chat_history: ChatHistory):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
def test_getitem(chat_history: ChatHistory):
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
def test_getitem(chat_history: ChatHistory):
=======
>>>>>>> Stashed changes
=======
def test_getitem(chat_history: ChatHistory):
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
def test_getitem(chat_history: ChatHistory):
=======
def test_getitem():
    chat_history = ChatHistory()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    content = "Message for index"
    chat_history.add_user_message(content)
    assert chat_history[0].content == content


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_contains(chat_history: ChatHistory):
    content = "Message to check"
    role = AuthorRole.USER
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def test_contains(chat_history: ChatHistory):
    content = "Message to check"
    role = AuthorRole.USER
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
def test_contains(chat_history: ChatHistory):
    content = "Message to check"
    role = AuthorRole.USER
=======
def test_contains():
    chat_history = ChatHistory()
    content = "Message to check"
    role = ChatRole.USER
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert message in chat_history


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_iter(chat_history: ChatHistory):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
def test_iter(chat_history: ChatHistory):
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
def test_iter(chat_history: ChatHistory):
=======
>>>>>>> Stashed changes
=======
def test_iter(chat_history: ChatHistory):
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
def test_iter(chat_history: ChatHistory):
=======
def test_iter():
    chat_history = ChatHistory()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    messages = ["Message 1", "Message 2"]
    for msg in messages:
        chat_history.add_user_message(msg)
    for i, message in enumerate(chat_history):
        assert message.content == messages[i]


def test_eq():
    # Create two instances of ChatHistory
    chat_history1 = ChatHistory()
    chat_history2 = ChatHistory()

    # Populate both instances with the same set of messages
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    messages = [("Message 1", AuthorRole.USER), ("Message 2", AuthorRole.ASSISTANT)]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    messages = [("Message 1", AuthorRole.USER), ("Message 2", AuthorRole.ASSISTANT)]
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    messages = [("Message 1", AuthorRole.USER), ("Message 2", AuthorRole.ASSISTANT)]
=======
>>>>>>> Stashed changes
=======
    messages = [("Message 1", AuthorRole.USER), ("Message 2", AuthorRole.ASSISTANT)]
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    messages = [("Message 1", AuthorRole.USER), ("Message 2", AuthorRole.ASSISTANT)]
=======
    messages = [("Message 1", ChatRole.USER), ("Message 2", ChatRole.ASSISTANT)]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    for content, role in messages:
        chat_history1.add_message({"role": role, "content": content})
        chat_history2.add_message({"role": role, "content": content})

    # Assert that the two instances are considered equal
    assert chat_history1 == chat_history2

    # Additionally, test inequality by adding an extra message to one of the histories
    chat_history1.add_user_message("Extra message")
    assert chat_history1 != chat_history2


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
def test_eq_invalid(chat_history: ChatHistory):
    # Populate both instances with the same set of messages
    messages = [("Message 1", AuthorRole.USER), ("Message 2", AuthorRole.ASSISTANT)]
    for content, role in messages:
        chat_history.add_message({"role": role, "content": content})

    assert chat_history != "other"


def test_dump():
    system_msg = "a test system prompt"
    chat_history = ChatHistory(
        messages=[ChatMessageContent(role=AuthorRole.USER, content="Message")],
        system_message=system_msg,
    )
    dump = chat_history.model_dump(exclude_none=True)
    assert dump is not None
    assert dump["messages"][0]["role"] == AuthorRole.SYSTEM
    assert dump["messages"][0]["items"][0]["text"] == system_msg
    assert dump["messages"][1]["role"] == AuthorRole.USER
    assert dump["messages"][1]["items"][0]["text"] == "Message"


def test_serialize():
    system_msg = "a test system prompt"
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(
                role=AuthorRole.USER,
                items=[
                    TextContent(text="Message"),
                    ImageContent(uri="http://test.com/image.jpg"),
                    ImageContent(data_uri="data:image/jpeg;base64,dGVzdF9kYXRh"),
                ],
            )
        ],
        system_message=system_msg,
    )

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
def test_eq_invalid():
    # Create two instances of ChatHistory
    chat_history1 = ChatHistory()

    # Populate both instances with the same set of messages
    messages = [("Message 1", ChatRole.USER), ("Message 2", ChatRole.ASSISTANT)]
    for content, role in messages:
        chat_history1.add_message({"role": role, "content": content})

    assert chat_history1 != "other"


def test_serialize():  # ignore: E501
    system_msg = "a test system prompt"
    chat_history = ChatHistory(
        messages=[ChatMessageContent(role=ChatRole.USER, content="Message")], system_message=system_msg
    )
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    json_str = chat_history.serialize()
    assert json_str is not None
    assert (
        json_str
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        == '{\n  "messages": [\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "system",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "a test system prompt"\n        }\n      ]\n    },\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "user",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "Message"\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "uri": "http://test.com/image.jpg",\n          "data_uri": ""\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "data_uri": "data:image/jpeg;base64,dGVzdF9kYXRh"\n        }\n      ]\n    }\n  ]\n}'  # noqa: E501
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        == '{\n  "messages": [\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "system",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "a test system prompt"\n        }\n      ]\n    },\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "user",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "Message"\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "uri": "http://test.com/image.jpg",\n          "data_uri": ""\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "data_uri": "data:image/jpeg;base64,dGVzdF9kYXRh"\n        }\n      ]\n    }\n  ]\n}'  # noqa: E501
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        == '{\n  "messages": [\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "system",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "a test system prompt"\n        }\n      ]\n    },\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "user",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "Message"\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "uri": "http://test.com/image.jpg",\n          "data_uri": ""\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "data_uri": "data:image/jpeg;base64,dGVzdF9kYXRh"\n        }\n      ]\n    }\n  ]\n}'  # noqa: E501
=======
>>>>>>> Stashed changes
=======
        == '{\n  "messages": [\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "system",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "a test system prompt"\n        }\n      ]\n    },\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "user",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "Message"\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "uri": "http://test.com/image.jpg",\n          "data_uri": ""\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "data_uri": "data:image/jpeg;base64,dGVzdF9kYXRh"\n        }\n      ]\n    }\n  ]\n}'  # noqa: E501
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        == '{\n  "messages": [\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "system",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "a test system prompt"\n        }\n      ]\n    },\n    {\n      "metadata": {},\n      "content_type": "message",\n      "role": "user",\n      "items": [\n        {\n          "metadata": {},\n          "content_type": "text",\n          "text": "Message"\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "uri": "http://test.com/image.jpg",\n          "data_uri": ""\n        },\n        {\n          "metadata": {},\n          "content_type": "image",\n          "data_uri": "data:image/jpeg;base64,dGVzdF9kYXRh"\n        }\n      ]\n    }\n  ]\n}'  # noqa: E501
=======
        == '{\n    "messages": [\n        {\n            \
"inner_content": null,\n            "ai_model_id": null,\n            \
"metadata": {},\n            "role": "system",\n            \
"content": "a test system prompt",\n            "encoding": null\n        },\
\n        {\n            "inner_content": null,\n            \
"ai_model_id": null,\n            "metadata": {},\n            \
"role": "user",\n            "content": "Message",\n            \
"encoding": null\n        }\n    ]\n}'
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    )


def test_serialize_and_deserialize_to_chat_history():
    system_msg = "a test system prompt"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    msgs = [
        ChatMessageContent(role=AuthorRole.USER, content=f"Message {i}")
        for i in range(3)
    ]
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
=======
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    chat_history = ChatHistory(messages=msgs, system_message=system_msg)
    json_str = chat_history.serialize()
    new_chat_history = ChatHistory.restore_chat_history(json_str)
    assert new_chat_history == chat_history


def test_deserialize_invalid_json_raises_exception():
    invalid_json = "invalid json"

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    with pytest.raises(ContentInitializationError):
        ChatHistory.restore_chat_history(invalid_json)


def test_chat_history_to_prompt_empty(chat_history: ChatHistory):
    prompt = str(chat_history)
    assert prompt == "<chat_history />"


def test_chat_history_to_prompt(chat_history: ChatHistory):
    chat_history.add_system_message("I am an AI assistant")
    chat_history.add_user_message("What can you do?")
    prompt = chat_history.to_prompt()
    assert (
        prompt
        == '<chat_history><message role="system"><text>I am an AI assistant</text></message><message role="user"><text>What can you do?</text></message></chat_history>'  # noqa: E501
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
    with pytest.raises(ValueError):
        ChatHistory.restore_chat_history(invalid_json)


def test_chat_history_to_prompt_empty():
    chat_history = ChatHistory()
    prompt = str(chat_history)
    assert prompt == ""


def test_chat_history_to_prompt():
    chat_history = ChatHistory()
    chat_history.add_system_message("I am an AI assistant")
    chat_history.add_user_message("What can you do?")
    prompt = str(chat_history)
    assert (
        prompt
        == '<message role="system">I am an AI assistant</message>\n<message role="user">What can you do?</message>'
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    )


def test_chat_history_from_rendered_prompt_empty():
    rendered = ""
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages == []


def test_chat_history_from_rendered_prompt():
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    rendered = '<message role="system"><text>I am an AI assistant</text></message><message role="user"><text>What can you do?</text></message>'  # noqa: E501

    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "I am an AI assistant"
    assert chat_history.messages[0].role == AuthorRole.SYSTEM
    assert chat_history.messages[1].content == "What can you do?"
    assert chat_history.messages[1].role == AuthorRole.USER
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    rendered = '<message role="system">I am an AI assistant</message>\n<message role="user">What can you do?</message>'

    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "I am an AI assistant"
    assert chat_history.messages[0].role == ChatRole.SYSTEM
    assert chat_history.messages[1].content == "What can you do?"
    assert chat_history.messages[1].role == ChatRole.USER
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


def test_chat_history_from_rendered_prompt_multi_line():
    rendered = """<message role="system">I am an AI assistant
and I can do 
stuff</message>
<message role="user">What can you do?</message>"""

    chat_history = ChatHistory.from_rendered_prompt(rendered)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    assert (
        chat_history.messages[0].content == "I am an AI assistant\nand I can do \nstuff"
    )
    assert chat_history.messages[0].role == AuthorRole.SYSTEM
    assert chat_history.messages[1].content == "What can you do?"
    assert chat_history.messages[1].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_template_unsafe(chat_history: ChatHistory):
    chat_history.add_assistant_message("I am an AI assistant")

    template = "system stuff{{$chat_history}}{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        ),
        allow_dangerously_set_content=True,
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history=chat_history, input="What can you do?"),
    )
    assert "system stuff" in rendered
    assert "I am an AI assistant" in rendered
    assert "What can you do?" in rendered

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "system stuff"
    assert chat_history_2.messages[0].role == AuthorRole.SYSTEM
    assert chat_history_2.messages[1].content == "I am an AI assistant"
    assert chat_history_2.messages[1].role == AuthorRole.ASSISTANT
    assert chat_history_2.messages[2].content == "What can you do?"
    assert chat_history_2.messages[2].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_template_safe(chat_history: ChatHistory):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
    assert chat_history.messages[0].content == "I am an AI assistant\nand I can do \nstuff"
    assert chat_history.messages[0].role == ChatRole.SYSTEM
    assert chat_history.messages[1].content == "What can you do?"
    assert chat_history.messages[1].role == ChatRole.USER


@pytest.mark.asyncio
async def test_template():
    chat_history = ChatHistory()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    chat_history.add_assistant_message("I am an AI assistant")

    template = "system stuff{{$chat_history}}{{$input}}"
    rendered = await KernelPromptTemplate(
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
=======
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history=chat_history, input="What can you do?"),
    )
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    assert "system stuff" in rendered
    assert "I am an AI assistant" in rendered
    assert "What can you do?" in rendered

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "system stuff"
    assert chat_history_2.messages[0].role == AuthorRole.SYSTEM
    assert chat_history_2.messages[1].content == "I am an AI assistant"
    assert chat_history_2.messages[1].role == AuthorRole.ASSISTANT
    assert chat_history_2.messages[2].content == "What can you do?"
    assert chat_history_2.messages[2].role == AuthorRole.USER
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
    assert rendered == 'system stuff<message role="assistant">I am an AI assistant</message>What can you do?'

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "system stuff"
    assert chat_history_2.messages[0].role == ChatRole.SYSTEM
    assert chat_history_2.messages[1].content == "I am an AI assistant"
    assert chat_history_2.messages[1].role == ChatRole.ASSISTANT
    assert chat_history_2.messages[2].content == "What can you do?"
    assert chat_history_2.messages[2].role == ChatRole.USER
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


@pytest.mark.asyncio
async def test_template_two_histories():  # ignore: E501
    chat_history1 = ChatHistory()
    chat_history1.add_assistant_message("I am an AI assistant")
    chat_history2 = ChatHistory()
    chat_history2.add_assistant_message("I like to be added later on")

    template = "system prompt{{$chat_history1}}{{$input}}{{$chat_history2}}"
    rendered = await KernelPromptTemplate(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(
            chat_history1=chat_history1,
            chat_history2=chat_history2,
            input="What can you do?",
        ),
    )
    assert "I am an AI assistant" in rendered
    assert "What can you do?" in rendered
    assert "I like to be added later on" in rendered

    chat_history_out = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_out.messages[0].content == "system prompt"
    assert chat_history_out.messages[0].role == AuthorRole.SYSTEM
    assert chat_history_out.messages[1].content == "I am an AI assistant"
    assert chat_history_out.messages[1].role == AuthorRole.ASSISTANT
    assert chat_history_out.messages[2].content == "What can you do?"
    assert chat_history_out.messages[2].role == AuthorRole.USER
    assert chat_history_out.messages[3].content == "I like to be added later on"
    assert chat_history_out.messages[3].role == AuthorRole.ASSISTANT
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history1=chat_history1, chat_history2=chat_history2, input="What can you do?"),
    )
    assert (
        rendered
        == 'system prompt<message role="assistant">I am an AI assistant</message>\
What can you do?<message role="assistant">I like to be added later on</message>'
    )

    chat_history_out = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_out.messages[0].content == "system prompt"
    assert chat_history_out.messages[0].role == ChatRole.SYSTEM
    assert chat_history_out.messages[1].content == "I am an AI assistant"
    assert chat_history_out.messages[1].role == ChatRole.ASSISTANT
    assert chat_history_out.messages[2].content == "What can you do?"
    assert chat_history_out.messages[2].role == ChatRole.USER
    assert chat_history_out.messages[3].content == "I like to be added later on"
    assert chat_history_out.messages[3].role == ChatRole.ASSISTANT
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


@pytest.mark.asyncio
async def test_template_two_histories_one_empty():
    chat_history1 = ChatHistory()
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< div
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    chat_history2 = ChatHistory()
    chat_history2.add_assistant_message("I am an AI assistant")

    template = "system prompt{{$chat_history1}}{{$input}}{{$chat_history2}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(
            chat_history1=chat_history1,
            chat_history2=chat_history2,
            input="What can you do?",
        ),
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
    chat_history1.add_assistant_message("I am an AI assistant")
    chat_history2 = ChatHistory()

    template = "system prompt{{$chat_history1}}{{$input}}{{$chat_history2}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history1=chat_history1, chat_history2=chat_history2, input="What can you do?"),
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    )

    chat_history_out = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_out.messages[0].content == "system prompt"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    assert chat_history_out.messages[0].role == AuthorRole.SYSTEM
    assert chat_history_out.messages[1].content == "What can you do?"
    assert chat_history_out.messages[1].role == AuthorRole.USER
    assert chat_history_out.messages[2].content == "I am an AI assistant"
    assert chat_history_out.messages[2].role == AuthorRole.ASSISTANT


@pytest.mark.asyncio
async def test_template_history_only(chat_history: ChatHistory):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    assert chat_history_out.messages[0].role == ChatRole.SYSTEM
    assert chat_history_out.messages[1].content == "I am an AI assistant"
    assert chat_history_out.messages[1].role == ChatRole.ASSISTANT
    assert chat_history_out.messages[2].content == "What can you do?"
    assert chat_history_out.messages[2].role == ChatRole.USER


@pytest.mark.asyncio
async def test_template_history_only():
    chat_history = ChatHistory()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    chat_history.add_assistant_message("I am an AI assistant")

    template = "{{$chat_history}}"
    rendered = await KernelPromptTemplate(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
=======
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    ).render(kernel=Kernel(), arguments=KernelArguments(chat_history=chat_history))

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "I am an AI assistant"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    assert chat_history_2.messages[0].role == AuthorRole.ASSISTANT
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    assert chat_history_2.messages[0].role == AuthorRole.ASSISTANT
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    assert chat_history_2.messages[0].role == AuthorRole.ASSISTANT
=======
>>>>>>> Stashed changes
=======
    assert chat_history_2.messages[0].role == AuthorRole.ASSISTANT
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    assert chat_history_2.messages[0].role == AuthorRole.ASSISTANT
=======
    assert chat_history_2.messages[0].role == ChatRole.ASSISTANT
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


@pytest.mark.asyncio
async def test_template_without_chat_history():
    template = "{{$input}}"
    rendered = await KernelPromptTemplate(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
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
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
=======
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    ).render(kernel=Kernel(), arguments=KernelArguments(input="What can you do?"))
    assert rendered == "What can you do?"
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "What can you do?"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    assert chat_history.messages[0].role == AuthorRole.USER
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    assert chat_history.messages[0].role == AuthorRole.USER
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    assert chat_history.messages[0].role == AuthorRole.USER
=======
>>>>>>> Stashed changes
=======
    assert chat_history.messages[0].role == AuthorRole.USER
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    assert chat_history.messages[0].role == AuthorRole.USER
=======
    assert chat_history.messages[0].role == ChatRole.SYSTEM
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


@pytest.mark.asyncio
async def test_handwritten_xml():
    template = '<message role="user">test content</message>'
    rendered = await KernelPromptTemplate(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
    ).render(kernel=Kernel(), arguments=KernelArguments())
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "test content"
    assert chat_history.messages[0].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_empty_text_content_message():
    template = '<message role="assistant"><text></text></message><message role="user">test content</message>'
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
    ).render(kernel=Kernel(), arguments=KernelArguments())
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].role == AuthorRole.ASSISTANT
    assert chat_history.messages[1].content == "test content"
    assert chat_history.messages[1].role == AuthorRole.USER
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(kernel=Kernel(), arguments=KernelArguments())
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "test content"
    assert chat_history.messages[0].role == ChatRole.USER
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


@pytest.mark.asyncio
async def test_handwritten_xml_invalid():
    template = '<message role="user"test content</message>'
    rendered = await KernelPromptTemplate(
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
    ).render(kernel=Kernel(), arguments=KernelArguments())
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert (
        chat_history.messages[0].content == '<message role="user"test content</message>'
    )
    assert chat_history.messages[0].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_handwritten_xml_as_arg_safe():
    template = "{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test",
            description="test",
            template=template,
        ),
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(input='<message role="user">test content</message>'),
    )
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert (
        chat_history.messages[0].content
        == '<message role="user">test content</message>'
    )
    assert chat_history.messages[0].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_handwritten_xml_as_arg_unsafe_template():
    template = "{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        ),
        allow_dangerously_set_content=True,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
>>>>>>> Stashed changes
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(kernel=Kernel(), arguments=KernelArguments())
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == '<message role="user"test content</message>'
    assert chat_history.messages[0].role == ChatRole.SYSTEM


@pytest.mark.asyncio
async def test_handwritten_xml_as_arg():
    template = "{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(input='<message role="user">test content</message>'),
    )
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "test content"
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    assert chat_history.messages[0].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_handwritten_xml_as_arg_unsafe_variable():
    template = "{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test",
            description="test",
            template=template,
            input_variables=[
                InputVariable(name="input", allow_dangerously_set_content=True)
            ],
        ),
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(input='<message role="user">test content</message>'),
    )
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "test content"
    assert chat_history.messages[0].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_template_empty_history(chat_history: ChatHistory):
    template = "system stuff{{$chat_history}}{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template
        )
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history=chat_history, input="What can you do?"),
    )

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "system stuff"
    assert chat_history_2.messages[0].role == AuthorRole.SYSTEM
    assert chat_history_2.messages[1].content == "What can you do?"
    assert chat_history_2.messages[1].role == AuthorRole.USER


def test_to_from_file(chat_history: ChatHistory, tmp_path):
    chat_history.add_system_message("You are an AI assistant")
    chat_history.add_user_message("What is the weather in Seattle?")
    chat_history.add_assistant_message(
        [
            FunctionCallContent(
                id="test1",
                name="WeatherPlugin-GetWeather",
                arguments='{{ "location": "Seattle" }}',
            )
        ]
    )
    chat_history.add_tool_message(
        [FunctionResultContent(id="test1", result="It is raining")]
    )
    chat_history.add_assistant_message(
        "It is raining in Seattle, what else can I help you with?"
    )

    file_path = tmp_path / "chat_history.json"
    chat_history.store_chat_history_to_file(file_path)
    chat_history_2 = ChatHistory.load_chat_history_from_file(file_path)
    assert len(chat_history_2.messages) == len(chat_history.messages)
    assert chat_history_2.messages[0] == chat_history.messages[0]
    assert chat_history_2.messages[1] == chat_history.messages[1]
    assert chat_history_2.messages[2] == chat_history.messages[2]
    assert chat_history_2.messages[3] == chat_history.messages[3]
    assert chat_history_2.messages[4] == chat_history.messages[4]


def test_chat_history_serialize(chat_history: ChatHistory):
    class CustomResultClass:
        def __init__(self, result):
            self.result = result

        def __str__(self) -> str:
            return self.result

    custom_result = CustomResultClass(result="CustomResultTestValue")
    chat_history.add_system_message("You are an AI assistant")
    chat_history.add_user_message("What is the weather in Seattle?")
    chat_history.add_assistant_message(
        [
            FunctionCallContent(
                id="test1",
                name="WeatherPlugin-GetWeather",
                arguments='{{ "location": "Seattle" }}',
            )
        ]
    )
    chat_history.add_tool_message(
        [FunctionResultContent(id="test1", result=custom_result)]
    )
    assert "CustomResultTestValue" in chat_history.serialize()
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
    assert chat_history.messages[0].role == ChatRole.USER


@pytest.mark.asyncio
async def test_history_openai_cmc():
    chat_history1 = ChatHistory()
    chat_history1.add_message(
        message=OpenAIChatMessageContent(
            inner_content=None,
            role=ChatRole.ASSISTANT,
            function_call=FunctionCall(name="test-test", arguments='{"input": "test"}'),
        )
    )
    template = "{{$chat_history}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history=chat_history1),
    )
    chat_history = ChatHistory.from_rendered_prompt(rendered, chat_message_content_type=OpenAIChatMessageContent)

    assert chat_history.messages[0].role == ChatRole.ASSISTANT
    assert chat_history.messages[0].function_call.name == "test-test"
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
