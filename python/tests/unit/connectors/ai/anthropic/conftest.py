# Copyright (c) Microsoft. All rights reserved.
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from anthropic import AsyncAnthropic
from anthropic.lib.streaming import TextEvent
from anthropic.lib.streaming._types import InputJsonEvent
from anthropic.types import (
    ContentBlockStopEvent,
    InputJSONDelta,
    Message,
    MessageDeltaUsage,
    MessageStopEvent,
    RawContentBlockDeltaEvent,
    RawContentBlockStartEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
    TextDelta,
    ToolUseBlock,
    Usage,
)
from anthropic.types.raw_message_delta_event import Delta

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_message_content import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)
from semantic_kernel.contents.const import ContentTypes
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent, StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason


@pytest.fixture
def mock_tool_calls_message() -> ChatMessageContent:
    return ChatMessageContent(
        ai_model_id="claude-3-opus-20240229",
        metadata={},
        content_type="message",
        role=AuthorRole.ASSISTANT,
        name=None,
        items=[
            TextContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type="text",
                text="<thinking></thinking>",
                encoding=None,
            ),
            FunctionCallContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.FUNCTION_CALL_CONTENT,
                id="test_function_call_content",
                index=1,
                name="math-Add",
                function_name="Add",
                plugin_name="math",
                arguments={"input": 3, "amount": 3},
            ),
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
def mock_parallel_tool_calls_message() -> ChatMessageContent:
    return ChatMessageContent(
        ai_model_id="claude-3-opus-20240229",
        metadata={},
        content_type="message",
        role=AuthorRole.ASSISTANT,
        name=None,
        items=[
            TextContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type="text",
                text="<thinking></thinking>",
                encoding=None,
            ),
            FunctionCallContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.FUNCTION_CALL_CONTENT,
                id="test_function_call_content_1",
                index=1,
                name="math-Add",
                function_name="Add",
                plugin_name="math",
                arguments={"input": 3, "amount": 3},
            ),
            FunctionCallContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.FUNCTION_CALL_CONTENT,
                id="test_function_call_content_2",
                index=1,
                name="math-Subtract",
                function_name="Subtract",
                plugin_name="math",
                arguments={"input": 6, "amount": 3},
            ),
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
def mock_streaming_tool_calls_message() -> list:
    stream_events = [
        RawMessageStartEvent(
            message=Message(
                id="test_message_id",
                content=[],
                model="claude-3-opus-20240229",
                role="assistant",
                stop_reason=None,
                stop_sequence=None,
                type="message",
                usage=Usage(input_tokens=1720, output_tokens=2),
            ),
            type="message_start",
        ),
        RawContentBlockStartEvent(content_block=TextBlock(text="", type="text"), index=0, type="content_block_start"),
        RawContentBlockDeltaEvent(
            delta=TextDelta(text="<thinking>", type="text_delta"), index=0, type="content_block_delta"
        ),
        TextEvent(type="text", text="<thinking>", snapshot="<thinking>"),
        RawContentBlockDeltaEvent(
            delta=TextDelta(text="</thinking>", type="text_delta"), index=0, type="content_block_delta"
        ),
        TextEvent(type="text", text="</thinking>", snapshot="<thinking></thinking>"),
        ContentBlockStopEvent(
            index=0, type="content_block_stop", content_block=TextBlock(text="<thinking></thinking>", type="text")
        ),
        RawContentBlockStartEvent(
            content_block=ToolUseBlock(id="test_tool_use_message_id", input={}, name="math-Add", type="tool_use"),
            index=1,
            type="content_block_start",
        ),
        RawContentBlockDeltaEvent(
            delta=InputJSONDelta(partial_json='{"input": 3, "amount": 3}', type="input_json_delta"),
            index=1,
            type="content_block_delta",
        ),
        InputJsonEvent(type="input_json", partial_json='{"input": 3, "amount": 3}', snapshot={"input": 3, "amount": 3}),
        ContentBlockStopEvent(
            index=1,
            type="content_block_stop",
            content_block=ToolUseBlock(
                id="test_tool_use_block_id", input={"input": 3, "amount": 3}, name="math-Add", type="tool_use"
            ),
        ),
        RawMessageDeltaEvent(
            delta=Delta(stop_reason="tool_use", stop_sequence=None),
            type="message_delta",
            usage=MessageDeltaUsage(output_tokens=159),
        ),
        MessageStopEvent(
            type="message_stop",
            message=Message(
                id="test_message_id",
                content=[
                    TextBlock(text="<thinking></thinking>", type="text"),
                    ToolUseBlock(
                        id="test_tool_use_block_id", input={"input": 3, "amount": 3}, name="math-Add", type="tool_use"
                    ),
                ],
                model="claude-3-opus-20240229",
                role="assistant",
                stop_reason="tool_use",
                stop_sequence=None,
                type="message",
                usage=Usage(input_tokens=100, output_tokens=100),
            ),
        ),
    ]

    async def async_generator():
        for event in stream_events:
            yield event

    stream_mock = AsyncMock()
    stream_mock.__aenter__.return_value = async_generator()

    return stream_mock


@pytest.fixture
def mock_tool_call_result_message() -> ChatMessageContent:
    return ChatMessageContent(
        inner_content=None,
        ai_model_id=None,
        metadata={},
        content_type="message",
        role=AuthorRole.TOOL,
        name=None,
        items=[
            FunctionResultContent(
                id="test_function_call_content",
                result=6,
            )
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
def mock_parallel_tool_call_result_message() -> ChatMessageContent:
    return ChatMessageContent(
        inner_content=None,
        ai_model_id=None,
        metadata={},
        content_type="message",
        role=AuthorRole.TOOL,
        name=None,
        items=[
            FunctionResultContent(
                id="test_function_call_content_1",
                result=6,
            ),
            FunctionResultContent(
                id="test_function_call_content_2",
                result=3,
            ),
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
def mock_streaming_chat_message_content() -> StreamingChatMessageContent:
    return StreamingChatMessageContent(
        choice_index=0,
        ai_model_id="claude-3-opus-20240229",
        metadata={},
        role=AuthorRole.ASSISTANT,
        name=None,
        items=[
            StreamingTextContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type="text",
                text="<thinking></thinking>",
                encoding=None,
                choice_index=0,
            ),
            FunctionCallContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.FUNCTION_CALL_CONTENT,
                id="tool_id",
                index=0,
                name="math-Add",
                function_name="Add",
                plugin_name="math",
                arguments='{"input": 3, "amount": 3}',
            ),
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
def mock_settings() -> AnthropicChatPromptExecutionSettings:
    return AnthropicChatPromptExecutionSettings()


@pytest.fixture
def mock_chat_message_response() -> Message:
    return Message(
        id="test_message_id",
        content=[TextBlock(text="Hello, how are you?", type="text")],
        model="claude-3-opus-20240229",
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=10, output_tokens=10),
    )


@pytest.fixture
def mock_streaming_message_response() -> AsyncGenerator:
    raw_message_start_event = RawMessageStartEvent(
        message=Message(
            id="test_message_id",
            content=[],
            model="claude-3-opus-20240229",
            role="assistant",
            stop_reason=None,
            stop_sequence=None,
            type="message",
            usage=Usage(input_tokens=41, output_tokens=3),
        ),
        type="message_start",
    )

    raw_content_block_start_event = RawContentBlockStartEvent(
        content_block=TextBlock(text="", type="text"),
        index=0,
        type="content_block_start",
    )

    raw_content_block_delta_event = RawContentBlockDeltaEvent(
        delta=TextDelta(text="Hello! It", type="text_delta"),
        index=0,
        type="content_block_delta",
    )

    text_event = TextEvent(
        type="text",
        text="Hello! It",
        snapshot="Hello! It",
    )

    content_block_stop_event = ContentBlockStopEvent(
        index=0,
        type="content_block_stop",
        content_block=TextBlock(text="Hello! It's nice to meet you.", type="text"),
    )

    raw_message_delta_event = RawMessageDeltaEvent(
        delta=Delta(stop_reason="end_turn", stop_sequence=None),
        type="message_delta",
        usage=MessageDeltaUsage(output_tokens=84),
    )

    message_stop_event = MessageStopEvent(
        type="message_stop",
        message=Message(
            id="test_message_stop_id",
            content=[TextBlock(text="Hello! It's nice to meet you.", type="text")],
            model="claude-3-opus-20240229",
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=Usage(input_tokens=41, output_tokens=84),
        ),
    )

    # Combine all mock events into a list
    stream_events = [
        raw_message_start_event,
        raw_content_block_start_event,
        raw_content_block_delta_event,
        text_event,
        content_block_stop_event,
        raw_message_delta_event,
        message_stop_event,
    ]

    async def async_generator():
        for event in stream_events:
            yield event

    # Create an AsyncMock for the stream
    stream_mock = AsyncMock()
    stream_mock.__aenter__.return_value = async_generator()

    return stream_mock


@pytest.fixture
def mock_anthropic_client_completion(mock_chat_message_response: Message) -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(return_value=mock_chat_message_response)
    client.messages = messages_mock
    return client


@pytest.fixture
def mock_anthropic_client_completion_stream(mock_streaming_message_response: AsyncGenerator) -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.return_value = mock_streaming_message_response
    client.messages = messages_mock
    return client
