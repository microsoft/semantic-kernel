# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai._streaming import AsyncStream
from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response import Response
from openai.types.responses.response_output_item_added_event import ResponseOutputItemAddedEvent
from openai.types.responses.response_output_item_done_event import ResponseOutputItemDoneEvent
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.response_text_delta_event import ResponseTextDeltaEvent

from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.agents.open_ai.responses_agent_thread_actions import ResponsesAgentThreadActions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole


@pytest.fixture
def mock_agent():
    agent = AsyncMock(spec=OpenAIResponsesAgent)
    agent.ai_model_id = "test-model-id"
    agent.name = "test-agent"
    agent.polling_options = MagicMock()
    agent.polling_options.default_polling_interval.total_seconds.return_value = 0.0001
    agent.tools = []
    agent.text = "auto"
    agent.temperature = 0.7
    agent.top_p = 1.0
    agent.metadata = {}
    agent.format_instructions = AsyncMock(return_value="base instructions")
    agent.kernel = MagicMock()
    agent.polling_options.run_polling_timeout.total_seconds.return_value = 5
    agent.polling_options.default_polling_interval.total_seconds.return_value = 1
    return agent


@pytest.fixture
def mock_response():
    response = MagicMock(spec=Response)
    response.status = "completed"
    response.output = []
    response.id = "fake-response-id"
    response.error = None
    response.incomplete_details = None
    response.created_at = 10303039393
    response.usage = None
    return response


@pytest.fixture
def mock_chat_history():
    history = MagicMock()
    history.messages = [ChatMessageContent(role=AuthorRole.USER, content="Hello")]
    return history


@pytest.fixture
def mock_thread():
    thread = MagicMock()
    thread._chat_history.messages = []
    return thread


@pytest.mark.asyncio
async def test_invoke_no_function_calls(mock_agent, mock_response, mock_chat_history, mock_thread):
    async def mock_get_response(*args, **kwargs):
        return mock_response

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        results = []
        async for is_visible, msg in ResponsesAgentThreadActions.invoke(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(),
        ):
            results.append((is_visible, msg))

    assert len(results) == 1
    is_visible, final_msg = results[0]
    assert is_visible is True
    assert final_msg.role == AuthorRole.ASSISTANT


@pytest.mark.asyncio
async def test_invoke_raises_on_failed_response(mock_agent, mock_chat_history, mock_thread):
    mock_failed_response = MagicMock(spec=Response)
    mock_failed_response.status = "failed"
    mock_failed_response.error = MagicMock()
    mock_failed_response.error.message = "some error"
    mock_failed_response.incomplete_details = None
    mock_failed_response.id = "fake-failed-response-id"

    async def mock_get_response(*args, **kwargs):
        return mock_failed_response

    with (
        patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response),
        pytest.raises(Exception, match="Run failed with status: `failed`"),
    ):
        async for _ in ResponsesAgentThreadActions.invoke(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(),
        ):
            pass


@pytest.mark.asyncio
async def test_invoke_reaches_maximum_attempts(mock_agent, mock_chat_history, mock_thread):
    call_counter = 0

    response_with_tool_call = MagicMock(spec=Response)
    response_with_tool_call.status = "completed"
    response_with_tool_call.id = "fake-response-id"
    response_with_tool_call.output = [
        ResponseFunctionToolCall(
            id="tool_call_id",
            call_id="call_id",
            name="test_function",
            arguments='{"some_arg": 123}',
            type="function_call",
        )
    ]
    response_with_tool_call.error = None
    response_with_tool_call.incomplete_details = None
    response_with_tool_call.created_at = 123456
    response_with_tool_call.usage = None
    response_with_tool_call.role = "assistant"

    final_response = MagicMock(spec=Response)
    final_response.status = "completed"
    final_response.id = "fake-final-response-id"
    final_response.output = []
    final_response.error = None
    final_response.incomplete_details = None
    final_response.created_at = 123456
    final_response.usage = None
    final_response.role = "assistant"

    async def mock_invoke_fc(*args, **kwargs):
        return MagicMock(terminate=False)

    mock_agent.kernel.invoke_function_call = MagicMock(side_effect=mock_invoke_fc)

    async def mock_get_response(*args, **kwargs):
        nonlocal call_counter
        if call_counter < 3:
            call_counter += 1
            return response_with_tool_call
        return final_response

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        messages = []
        async for _, msg in ResponsesAgentThreadActions.invoke(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(maximum_auto_invoke_attempts=3),
        ):
            messages.append(msg)

        assert messages is not None


@pytest.mark.asyncio
async def test_invoke_with_function_calls(mock_agent, mock_chat_history, mock_thread):
    initial_response = MagicMock(spec=Response)
    initial_response.status = "completed"
    initial_response.id = "fake-response-id"
    initial_response.output = [
        ResponseFunctionToolCall(
            id="tool_call_id",
            call_id="call_id",
            name="test_function",
            arguments='{"some_arg": 123}',
            type="function_call",
        )
    ]
    initial_response.error = None
    initial_response.incomplete_details = None
    initial_response.created_at = 123456
    initial_response.usage = None
    initial_response.role = "assistant"

    final_response = MagicMock(spec=Response)
    final_response.status = "completed"
    final_response.id = "fake-final-response-id"
    final_response.output = []
    final_response.error = None
    final_response.incomplete_details = None
    final_response.created_at = 123456
    final_response.usage = None
    final_response.role = "assistant"

    responses = [initial_response, final_response]

    async def mock_invoke_fc(*args, **kwargs):
        return MagicMock(terminate=False)

    mock_agent.kernel.invoke_function_call = MagicMock(side_effect=mock_invoke_fc)

    async def mock_get_response(*args, **kwargs):
        return responses.pop(0)

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        messages = []
        async for is_visible, msg in ResponsesAgentThreadActions.invoke(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(maximum_auto_invoke_attempts=1),
        ):
            messages.append(msg)

        assert len(messages) == 3, f"Expected exactly 3 messages, got {len(messages)}"


async def test_invoke_stream_no_function_calls(mock_agent, mock_chat_history, mock_thread):
    class MockStream(AsyncStream[ResponseStreamEvent]):
        def __init__(self, events):
            self._events = events

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._events:
                raise StopAsyncIteration
            return self._events.pop(0)

    mock_stream_event = ResponseTextDeltaEvent(
        delta="Test partial content",
        content_index=0,
        item_id="fake-item-id",
        output_index=0,
        type="response.output_text.delta",
    )

    mock_stream_event_end = ResponseOutputItemDoneEvent(
        item=ResponseOutputMessage(
            role="assistant",
            status="completed",
            id="fake-item-id",
            content=[ResponseOutputText(text="Test partial content", type="output_text", annotations=[])],
            type="message",
        ),
        output_index=0,
        type="response.output_item.done",
    )

    async def mock_get_response(*args, **kwargs):
        return MockStream([mock_stream_event, mock_stream_event_end])

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        collected_stream_messages = []
        received_text = ""

        async for streaming_msg in ResponsesAgentThreadActions.invoke_stream(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=False,
            function_choice_behavior=MagicMock(),
            output_messages=collected_stream_messages,
        ):
            assert isinstance(streaming_msg, StreamingChatMessageContent)
            for item in streaming_msg.items:
                if isinstance(item, StreamingTextContent):
                    received_text += item.text

        assert "Test partial content" in received_text, "Expected streamed partial content."
        assert len(collected_stream_messages) == 1, "Expected exactly one final message."
        assert collected_stream_messages[0].role == AuthorRole.ASSISTANT


@pytest.mark.asyncio
async def test_invoke_stream_with_tool_calls(mock_agent, mock_chat_history, mock_thread):
    class MockStream(AsyncStream[ResponseStreamEvent]):
        def __init__(self, events):
            self._events = events

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        def __aiter__(self):
            return self

        async def __anext__(self):
            if not self._events:
                raise StopAsyncIteration
            return self._events.pop(0)

    mock_tool_call_event = ResponseOutputItemAddedEvent(
        item=ResponseFunctionToolCall(
            id="fake-tool-call-id",
            call_id="fake-call-id",
            name="test_function",
            arguments='{"arg": 123}',
            type="function_call",
        ),
        output_index=0,
        type="response.output_item.added",
    )

    mock_stream_event_end = ResponseOutputItemDoneEvent(
        item=ResponseOutputMessage(
            role="assistant",
            status="completed",
            id="fake-item-id",
            content=[ResponseOutputText(text="Final message after tool call", type="output_text", annotations=[])],
            type="message",
        ),
        output_index=0,
        type="response.output_item.done",
    )

    async def mock_get_response(*args, **kwargs):
        return MockStream([mock_tool_call_event, mock_stream_event_end])

    async def mock_invoke_function_call(*args, **kwargs):
        return MagicMock(terminate=False)

    mock_agent.kernel.invoke_function_call = MagicMock(side_effect=mock_invoke_function_call)

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        collected_stream_messages = []
        received_text = ""

        async for streaming_msg in ResponsesAgentThreadActions.invoke_stream(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(maximum_auto_invoke_attempts=1),
            output_messages=collected_stream_messages,
        ):
            assert isinstance(streaming_msg, StreamingChatMessageContent)
            for item in streaming_msg.items:
                if isinstance(item, StreamingTextContent):
                    received_text += item.text

        assert len(collected_stream_messages) == 2, "Expected exactly two final messages after tool call."
        assert collected_stream_messages[0].role == AuthorRole.ASSISTANT
