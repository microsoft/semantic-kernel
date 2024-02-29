# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.exceptions import ContentInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_init_with_system_message_only():
    system_msg = "test message"
    chat_history = ChatHistory(system_message=system_msg)
    assert len(chat_history.messages) == 1
    assert chat_history.messages[0].content == system_msg


def test_init_with_messages_only():
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
    chat_history = ChatHistory(messages=msgs)
    assert chat_history.messages == msgs, "Chat history should contain exactly the provided messages"


def test_init_with_messages_and_system_message():
    system_msg = "a test system prompt"
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
    with pytest.raises(ContentInitializationError):
        chat_history.add_message(message={"content": content})


def test_add_message_invalid_type():
    chat_history = ChatHistory()
    content = "Test message"
    with pytest.raises(ContentInitializationError):
        chat_history.add_message(message=content)


def test_remove_message():
    chat_history = ChatHistory()
    content = "Message to remove"
    role = ChatRole.USER
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert chat_history.remove_message(message) is True
    assert message not in chat_history.messages


def test_remove_message_invalid():
    chat_history = ChatHistory()
    content = "Message to remove"
    role = ChatRole.USER
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert chat_history.remove_message("random") is False


def test_len():
    chat_history = ChatHistory()
    content = "Message"
    chat_history.add_user_message(content)
    chat_history.add_system_message(content)
    assert len(chat_history) == 2


def test_getitem():
    chat_history = ChatHistory()
    content = "Message for index"
    chat_history.add_user_message(content)
    assert chat_history[0].content == content


def test_contains():
    chat_history = ChatHistory()
    content = "Message to check"
    role = ChatRole.USER
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert message in chat_history


def test_iter():
    chat_history = ChatHistory()
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
    messages = [("Message 1", ChatRole.USER), ("Message 2", ChatRole.ASSISTANT)]
    for content, role in messages:
        chat_history1.add_message({"role": role, "content": content})
        chat_history2.add_message({"role": role, "content": content})

    # Assert that the two instances are considered equal
    assert chat_history1 == chat_history2

    # Additionally, test inequality by adding an extra message to one of the histories
    chat_history1.add_user_message("Extra message")
    assert chat_history1 != chat_history2


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
    json_str = chat_history.serialize()
    assert json_str is not None
    assert (
        json_str
        == '{\n    "messages": [\n        {\n            \
"inner_content": null,\n            "ai_model_id": null,\n            \
"metadata": {},\n            "role": "system",\n            \
"content": "a test system prompt",\n            "encoding": null\n        },\
\n        {\n            "inner_content": null,\n            \
"ai_model_id": null,\n            "metadata": {},\n            \
"role": "user",\n            "content": "Message",\n            \
"encoding": null\n        }\n    ]\n}'
    )


def test_serialize_and_deserialize_to_chat_history():
    system_msg = "a test system prompt"
    msgs = [ChatMessageContent(role=ChatRole.USER, content=f"Message {i}") for i in range(3)]
    chat_history = ChatHistory(messages=msgs, system_message=system_msg)
    json_str = chat_history.serialize()
    new_chat_history = ChatHistory.restore_chat_history(json_str)
    assert new_chat_history == chat_history


def test_deserialize_invalid_json_raises_exception():
    invalid_json = "invalid json"

    with pytest.raises(ContentInitializationError):
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
    )


def test_chat_history_from_rendered_prompt_empty():
    rendered = ""
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages == []


def test_chat_history_from_rendered_prompt():
    rendered = '<message role="system">I am an AI assistant</message>\n<message role="user">What can you do?</message>'

    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "I am an AI assistant"
    assert chat_history.messages[0].role == ChatRole.SYSTEM
    assert chat_history.messages[1].content == "What can you do?"
    assert chat_history.messages[1].role == ChatRole.USER


def test_chat_history_from_rendered_prompt_multi_line():
    rendered = """<message role="system">I am an AI assistant
and I can do 
stuff</message>
<message role="user">What can you do?</message>"""

    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "I am an AI assistant\nand I can do \nstuff"
    assert chat_history.messages[0].role == ChatRole.SYSTEM
    assert chat_history.messages[1].content == "What can you do?"
    assert chat_history.messages[1].role == ChatRole.USER


@pytest.mark.asyncio
async def test_template():
    chat_history = ChatHistory()
    chat_history.add_assistant_message("I am an AI assistant")

    template = "system stuff{{$chat_history}}{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history=chat_history, input="What can you do?"),
    )
    assert rendered == 'system stuff<message role="assistant">I am an AI assistant</message>What can you do?'

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "system stuff"
    assert chat_history_2.messages[0].role == ChatRole.SYSTEM
    assert chat_history_2.messages[1].content == "I am an AI assistant"
    assert chat_history_2.messages[1].role == ChatRole.ASSISTANT
    assert chat_history_2.messages[2].content == "What can you do?"
    assert chat_history_2.messages[2].role == ChatRole.USER


@pytest.mark.asyncio
async def test_template_two_histories():  # ignore: E501
    chat_history1 = ChatHistory()
    chat_history1.add_assistant_message("I am an AI assistant")
    chat_history2 = ChatHistory()
    chat_history2.add_assistant_message("I like to be added later on")

    template = "system prompt{{$chat_history1}}{{$input}}{{$chat_history2}}"
    rendered = await KernelPromptTemplate(
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


@pytest.mark.asyncio
async def test_template_two_histories_one_empty():
    chat_history1 = ChatHistory()
    chat_history1.add_assistant_message("I am an AI assistant")
    chat_history2 = ChatHistory()

    template = "system prompt{{$chat_history1}}{{$input}}{{$chat_history2}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(chat_history1=chat_history1, chat_history2=chat_history2, input="What can you do?"),
    )

    chat_history_out = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_out.messages[0].content == "system prompt"
    assert chat_history_out.messages[0].role == ChatRole.SYSTEM
    assert chat_history_out.messages[1].content == "I am an AI assistant"
    assert chat_history_out.messages[1].role == ChatRole.ASSISTANT
    assert chat_history_out.messages[2].content == "What can you do?"
    assert chat_history_out.messages[2].role == ChatRole.USER


@pytest.mark.asyncio
async def test_template_history_only():
    chat_history = ChatHistory()
    chat_history.add_assistant_message("I am an AI assistant")

    template = "{{$chat_history}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(kernel=Kernel(), arguments=KernelArguments(chat_history=chat_history))

    chat_history_2 = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history_2.messages[0].content == "I am an AI assistant"
    assert chat_history_2.messages[0].role == ChatRole.ASSISTANT


@pytest.mark.asyncio
async def test_template_without_chat_history():
    template = "{{$input}}"
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(kernel=Kernel(), arguments=KernelArguments(input="What can you do?"))
    assert rendered == "What can you do?"
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "What can you do?"
    assert chat_history.messages[0].role == ChatRole.SYSTEM


@pytest.mark.asyncio
async def test_handwritten_xml():
    template = '<message role="user">test content</message>'
    rendered = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template=template)
    ).render(kernel=Kernel(), arguments=KernelArguments())
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "test content"
    assert chat_history.messages[0].role == ChatRole.USER


@pytest.mark.asyncio
async def test_handwritten_xml_invalid():
    template = '<message role="user"test content</message>'
    rendered = await KernelPromptTemplate(
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
    ).render(
        kernel=Kernel(),
        arguments=KernelArguments(input='<message role="user">test content</message>'),
    )
    chat_history = ChatHistory.from_rendered_prompt(rendered)
    assert chat_history.messages[0].content == "test content"
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
