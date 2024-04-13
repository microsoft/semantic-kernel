from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_message_content_base import ChatMessageContentBase
from semantic_kernel.contents.chat_role import ChatRole


def test_cmc():
    message = ChatMessageContent(role="user", content="Hello, world!")
    assert message.type == "ChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.model_fields_set == {"role", "content"}


def test_oai_cmc():
    message = OpenAIChatMessageContent(
        role="user", content="Hello, world!", function_call=FunctionCall(), tool_calls=[ToolCall()], tool_call_id="1234"
    )
    assert message.type == "OpenAIChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.function_call == FunctionCall()
    assert message.tool_calls == [ToolCall()]
    assert message.tool_call_id == "1234"
    assert message.model_fields_set == {"role", "content", "function_call", "tool_calls", "tool_call_id"}


def test_aoai_cmc():
    message = AzureChatMessageContent(
        role="user",
        content="Hello, world!",
        function_call=FunctionCall(),
        tool_calls=[ToolCall()],
        tool_call_id="1234",
        tool_message="test",
    )
    assert message.type == "AzureChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.function_call == FunctionCall()
    assert message.tool_calls == [ToolCall()]
    assert message.tool_call_id == "1234"
    assert message.tool_message == "test"
    assert message.model_fields_set == {
        "role",
        "content",
        "function_call",
        "tool_calls",
        "tool_call_id",
        "tool_message",
    }


def test_cmc_from_root_model_from_fields():
    message = ChatMessageContentBase.from_fields(role="user", content="Hello, world!", type="ChatMessageContent")
    assert message.type == "ChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.model_fields_set == {"role", "content", "type"}


def test_cmc_from_root_model_from_dict():
    message = ChatMessageContentBase.from_dict(
        {"role": "user", "content": "Hello, world!", "type": "ChatMessageContent"}
    )
    assert message.type == "ChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.model_fields_set == {"role", "content", "type"}


def test_oai_cmc_from_root_model():
    message = ChatMessageContentBase.from_fields(
        role="user",
        content="Hello, world!",
        function_call=FunctionCall(),
        tool_calls=[ToolCall()],
        tool_call_id="1234",
        type="OpenAIChatMessageContent",
    )
    assert message.type == "OpenAIChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.function_call == FunctionCall()
    assert message.tool_calls == [ToolCall()]
    assert message.tool_call_id == "1234"
    assert message.model_fields_set == {"role", "content", "function_call", "tool_calls", "tool_call_id", "type"}


def test_aoai_cmc_from_root_model():
    message = ChatMessageContentBase.from_fields(
        role="user",
        content="Hello, world!",
        function_call=FunctionCall(),
        tool_calls=[ToolCall()],
        tool_call_id="1234",
        tool_message="test",
        type="AzureChatMessageContent",
    )
    assert message.type == "AzureChatMessageContent"
    assert message.role == ChatRole.USER
    assert message.content == "Hello, world!"
    assert message.function_call == FunctionCall()
    assert message.tool_calls == [ToolCall()]
    assert message.tool_call_id == "1234"
    assert message.tool_message == "test"
    assert message.model_fields_set == {
        "role",
        "content",
        "function_call",
        "tool_calls",
        "tool_call_id",
        "tool_message",
        "type",
    }
