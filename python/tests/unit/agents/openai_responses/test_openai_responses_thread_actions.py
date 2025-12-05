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
from openai.types.responses.response_text_delta_event import Logprob, ResponseTextDeltaEvent

from semantic_kernel.agents.open_ai.openai_responses_agent import OpenAIResponsesAgent
from semantic_kernel.agents.open_ai.responses_agent_thread_actions import ResponsesAgentThreadActions
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments


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


async def test_invoke_passes_kernel_arguments_to_kernel(mock_agent, mock_chat_history, mock_thread):
    # Prepare a response that triggers a function call
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
        # Assert that KernelArguments were forwarded
        assert isinstance(kwargs.get("arguments"), KernelArguments)
        assert kwargs["arguments"].get("foo") == "bar"
        return MagicMock(terminate=False)

    mock_agent.kernel.invoke_function_call = MagicMock(side_effect=mock_invoke_fc)

    async def mock_get_response(*args, **kwargs):
        return responses.pop(0)

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        args = KernelArguments(foo="bar")
        # Run invoke and ensure no assertion fails inside mock_invoke_fc
        collected = []
        async for _, msg in ResponsesAgentThreadActions.invoke(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(maximum_auto_invoke_attempts=1),
            arguments=args,
        ):
            collected.append(msg)
        assert len(collected) >= 2


async def test_invoke_stream_passes_kernel_arguments_to_kernel(mock_agent, mock_chat_history, mock_thread):
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

    # Event that includes a function call
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
        sequence_number=0,
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
        sequence_number=0,
        type="response.output_item.done",
    )

    async def mock_get_response(*args, **kwargs):
        return MockStream([mock_tool_call_event, mock_stream_event_end])

    async def mock_invoke_function_call(*args, **kwargs):
        assert isinstance(kwargs.get("arguments"), KernelArguments)
        assert kwargs["arguments"].get("foo") == "bar"
        return MagicMock(terminate=False)

    mock_agent.kernel.invoke_function_call = MagicMock(side_effect=mock_invoke_function_call)

    with patch.object(ResponsesAgentThreadActions, "_get_response", new=mock_get_response):
        args = KernelArguments(foo="bar")
        collected_stream_messages = []
        async for _ in ResponsesAgentThreadActions.invoke_stream(
            agent=mock_agent,
            chat_history=mock_chat_history,
            thread=mock_thread,
            store_enabled=True,
            function_choice_behavior=MagicMock(maximum_auto_invoke_attempts=1),
            output_messages=collected_stream_messages,
            arguments=args,
        ):
            pass
        # If assertions passed in mock, arguments were forwarded
        assert len(collected_stream_messages) >= 1


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
        logprobs=[Logprob(token="test_token", logprob=0.3)],
        output_index=0,
        type="response.output_text.delta",
        sequence_number=0,
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
        sequence_number=0,
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
        sequence_number=0,
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
        sequence_number=0,
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


def test_get_tools(mock_agent, kernel, custom_plugin_class):
    kernel.add_plugin(custom_plugin_class)
    fcb = FunctionChoiceBehavior()
    tools = ResponsesAgentThreadActions._get_tools(
        agent=mock_agent,
        kernel=kernel,
        function_choice_behavior=fcb,
    )

    assert len(tools) == len(mock_agent.tools) + len(kernel.get_full_list_of_function_metadata())


def test_prepare_chat_history_multiple_images_no_duplication():
    """Test that multiple images in a message don't get duplicated in the request."""
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.image_content import ImageContent
    from semantic_kernel.contents.text_content import TextContent

    # Create a chat history with a message containing text and multiple images
    chat_history = ChatHistory()

    message_items = [
        TextContent(text="How many pictures do you get?"),
        ImageContent(uri="https://example.com/image1.jpg"),
        ImageContent(uri="https://example.com/image2.jpg"),
        ImageContent(uri="https://example.com/image3.jpg"),
        ImageContent(uri="https://example.com/image4.jpg"),
    ]

    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.utils.author_role import AuthorRole

    message = ChatMessageContent(role=AuthorRole.USER, items=message_items)
    chat_history.add_message(message)

    # Call the method that was causing duplication
    result = ResponsesAgentThreadActions._prepare_chat_history_for_request(chat_history, True)

    # Verify we have exactly one message in the result
    assert len(result) == 1, f"Expected 1 message, got {len(result)}"

    # Get the content from the message
    message_content = result[0]["content"]

    # Count text and image items
    text_items = [item for item in message_content if item["type"] == "input_text"]
    image_items = [item for item in message_content if item["type"] == "input_image"]

    # Verify counts
    assert len(text_items) == 1, f"Expected 1 text item, got {len(text_items)}"
    assert len(image_items) == 4, f"Expected 4 image items, got {len(image_items)}"

    # Verify the text content
    assert text_items[0]["text"] == "How many pictures do you get?"

    # Verify the image URLs are correct and not duplicated
    expected_urls = [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg",
        "https://example.com/image4.jpg",
    ]

    actual_urls = [item["image_url"] for item in image_items]
    assert actual_urls == expected_urls, f"Expected {expected_urls}, got {actual_urls}"

    # Verify total content items equals expected (1 text + 4 images = 5)
    assert len(message_content) == 5, f"Expected 5 total content items, got {len(message_content)}"
