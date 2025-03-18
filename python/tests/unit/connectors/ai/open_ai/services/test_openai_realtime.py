# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import AsyncIterable
from typing import Any
from unittest.mock import AsyncMock, patch

from aiortc import AudioStreamTrack
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection, AsyncRealtimeConnectionManager
from openai.types.beta.realtime import (
    ConversationItem,
    ConversationItemContent,
    ConversationItemCreatedEvent,
    ConversationItemCreateEvent,
    ConversationItemDeletedEvent,
    ConversationItemDeleteEvent,
    ConversationItemTruncatedEvent,
    ConversationItemTruncateEvent,
    ErrorEvent,
    InputAudioBufferAppendEvent,
    InputAudioBufferClearedEvent,
    InputAudioBufferClearEvent,
    InputAudioBufferCommitEvent,
    InputAudioBufferCommittedEvent,
    InputAudioBufferSpeechStartedEvent,
    RealtimeResponse,
    RealtimeServerEvent,
    ResponseAudioDeltaEvent,
    ResponseAudioDoneEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseCancelEvent,
    ResponseCreatedEvent,
    ResponseCreateEvent,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseOutputItemAddedEvent,
    Session,
    SessionCreatedEvent,
    SessionUpdatedEvent,
    SessionUpdateEvent,
)
from pytest import fixture, mark, param, raises

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    OpenAIRealtimeExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_realtime import (
    ListenEvents,
    OpenAIRealtimeWebRTC,
    OpenAIRealtimeWebsocket,
    SendEvents,
    _create_openai_realtime_client_event,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.realtime_events import (
    RealtimeAudioEvent,
    RealtimeEvent,
    RealtimeFunctionCallEvent,
    RealtimeFunctionResultEvent,
    RealtimeTextEvent,
)
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.content_exceptions import ContentException
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

events = [
    SessionCreatedEvent(type=ListenEvents.SESSION_CREATED, session=Session(id="session_id"), event_id="1"),
    SessionUpdatedEvent(type=ListenEvents.SESSION_UPDATED, session=Session(id="session_id"), event_id="2"),
    ConversationItemCreatedEvent(
        type=ListenEvents.CONVERSATION_ITEM_CREATED,
        item=ConversationItem(id="item_id"),
        event_id="3",
        previous_item_id="2",
    ),
    ConversationItemDeletedEvent(type=ListenEvents.CONVERSATION_ITEM_DELETED, item_id="item_id", event_id="4"),
    ConversationItemTruncatedEvent(
        type=ListenEvents.CONVERSATION_ITEM_TRUNCATED, event_id="5", audio_end_ms=0, content_index=0, item_id="item_id"
    ),
    InputAudioBufferClearedEvent(type=ListenEvents.INPUT_AUDIO_BUFFER_CLEARED, event_id="7"),
    InputAudioBufferCommittedEvent(
        type=ListenEvents.INPUT_AUDIO_BUFFER_COMMITTED,
        event_id="8",
        item_id="item_id",
        previous_item_id="previous_item_id",
    ),
    ResponseCreatedEvent(type=ListenEvents.RESPONSE_CREATED, event_id="10", response=RealtimeResponse()),
    ResponseFunctionCallArgumentsDoneEvent(
        type=ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE,
        event_id="11",
        arguments="{}",
        call_id="call_id",
        item_id="item_id",
        output_index=0,
        response_id="response_id",
    ),
    ResponseAudioTranscriptDeltaEvent(
        type=ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA,
        event_id="12",
        content_index=0,
        delta="text",
        item_id="item_id",
        output_index=0,
        response_id="response_id",
    ),
    ResponseAudioDoneEvent(
        type=ListenEvents.RESPONSE_AUDIO_DONE,
        event_id="13",
        item_id="item_id",
        output_index=0,
        response_id="response_id",
        content_index=0,
    ),
    ResponseAudioDeltaEvent(
        type=ListenEvents.RESPONSE_AUDIO_DELTA,
        event_id="14",
        item_id="item_id",
        output_index=0,
        response_id="response_id",
        content_index=0,
        delta="audio data",
    ),
]


async def websocket_stream(**kwargs) -> AsyncIterable[RealtimeServerEvent]:
    for event in events:
        yield event
    await asyncio.sleep(0)


@fixture
def audio_track():
    class AudioTrack(AudioStreamTrack):
        kind = "audio"

        async def recv(self):
            await asyncio.sleep(0)
            return

    return AudioTrack()


@fixture
def OpenAIWebsocket(openai_unit_test_env):
    client = OpenAIRealtimeWebsocket()
    client._call_id_to_function_map["call_id"] = "function_name"
    return client


@fixture
def OpenAIWebRTC(openai_unit_test_env, audio_track):
    client = OpenAIRealtimeWebRTC(audio_track=audio_track)
    client._call_id_to_function_map["call_id"] = "function_name"
    return client


def test_update_settings_from_function_call_config():
    config = FunctionCallChoiceConfiguration(
        available_functions=[
            KernelFunctionMetadata(name="function_name", description="function_description", is_prompt=False)
        ]
    )

    settings = OpenAIRealtimeExecutionSettings()

    update_settings_from_function_call_configuration(config, settings, FunctionChoiceType.AUTO)

    assert len(settings.tools) == 1
    assert settings.tools[0]["type"] == "function"
    assert settings.tools[0]["name"] == "function_name"
    assert settings.tools[0]["description"] == "function_description"
    assert settings.tool_choice == FunctionChoiceType.AUTO.value


def test_openai_realtime_websocket(openai_unit_test_env):
    realtime_client = OpenAIRealtimeWebsocket()
    assert realtime_client is not None


def test_openai_realtime_webrtc(openai_unit_test_env, audio_track):
    realtime_client = OpenAIRealtimeWebRTC(audio_track=audio_track)
    assert realtime_client is not None


@mark.parametrize(
    ["event_type", "event_kwargs", "expected_event", "expected_exception"],
    [
        param(
            SendEvents.SESSION_UPDATE,
            {"session": {"id": "session_id"}},
            SessionUpdateEvent,
            None,
            id="session_update",
        ),
        param(
            SendEvents.SESSION_UPDATE,
            {},
            SessionUpdateEvent,
            ContentException,
            id="session_update_missing",
        ),
        param(
            SendEvents.INPUT_AUDIO_BUFFER_APPEND,
            {"audio": "audio_buffer_as_string"},
            InputAudioBufferAppendEvent,
            None,
            id="input_audio_buffer_append",
        ),
        param(
            SendEvents.INPUT_AUDIO_BUFFER_APPEND,
            {},
            InputAudioBufferAppendEvent,
            ContentException,
            id="input_audio_buffer_append_missing_audio",
        ),
        param(
            SendEvents.INPUT_AUDIO_BUFFER_COMMIT,
            {},
            InputAudioBufferCommitEvent,
            None,
            id="input_audio_buffer_commit",
        ),
        param(
            SendEvents.INPUT_AUDIO_BUFFER_CLEAR,
            {},
            InputAudioBufferClearEvent,
            None,
            id="input_audio_buffer_Clear",
        ),
        param(
            SendEvents.CONVERSATION_ITEM_CREATE,
            {
                "event_id": "event_id",
                "previous_item_id": "previous_item_id",
                "item": {"id": "item_id"},
            },
            ConversationItemCreateEvent,
            None,
            id="conversation_item_create_event",
        ),
        param(
            SendEvents.CONVERSATION_ITEM_CREATE,
            {},
            ConversationItemCreateEvent,
            ContentException,
            id="conversation_item_create_event_no_item",
        ),
        param(
            SendEvents.CONVERSATION_ITEM_TRUNCATE,
            {"audio_end_ms": 1000, "item_id": "item_id"},
            ConversationItemTruncateEvent,
            None,
            id="conversation_item_truncate",
        ),
        param(
            SendEvents.CONVERSATION_ITEM_DELETE,
            {"item_id": "item_id"},
            ConversationItemDeleteEvent,
            None,
            id="conversation_item_delete",
        ),
        param(
            SendEvents.CONVERSATION_ITEM_DELETE,
            {},
            ConversationItemDeleteEvent,
            ContentException,
            id="conversation_item_delete_fail",
        ),
        param(
            SendEvents.RESPONSE_CREATE,
            {"response": {"instructions": "instructions"}},
            ResponseCreateEvent,
            None,
            id="response_create",
        ),
        param(
            SendEvents.RESPONSE_CANCEL,
            {},
            ResponseCancelEvent,
            None,
            id="response_cancel",
        ),
    ],
)
def test_create_openai_realtime_event(
    event_type: SendEvents, event_kwargs: dict[str, Any], expected_event: Any, expected_exception: Exception | None
):
    if expected_exception:
        with raises(expected_exception):
            _create_openai_realtime_client_event(event_type, **event_kwargs)
    else:
        event = _create_openai_realtime_client_event(event_type, **event_kwargs)
        assert isinstance(event, expected_event)


@mark.parametrize(
    ["event", "expected_type"],
    [
        param(
            ResponseAudioTranscriptDeltaEvent(
                content_index=0,
                delta="text",
                item_id="item_id",
                event_id="event_id",
                output_index=0,
                response_id="response_id",
                type="response.audio_transcript.delta",
            ),
            [RealtimeTextEvent],
            id="response_audio_transcript_delta",
        ),
        param(
            ResponseOutputItemAddedEvent(
                item=ConversationItem(id="item_id"),
                event_id="event_id",
                output_index=0,
                response_id="response_id",
                type="response.output_item.added",
            ),
            [RealtimeEvent],
            id="response_output_item_added",
        ),
        param(
            ResponseOutputItemAddedEvent(
                item=ConversationItem(id="item_id", type="function_call", call_id="call_id", name="function_to_call"),
                event_id="event_id",
                output_index=0,
                response_id="response_id",
                type="response.output_item.added",
            ),
            [RealtimeEvent],
            id="response_output_item_added_function_call",
        ),
        param(
            ResponseFunctionCallArgumentsDeltaEvent(
                call_id="call_id",
                delta="argument delta",
                event_id="event_id",
                output_index=0,
                item_id="item_id",
                response_id="response_id",
                type="response.function_call_arguments.delta",
            ),
            [RealtimeFunctionCallEvent],
            id="response_function_call_arguments_delta",
        ),
        param(
            ResponseFunctionCallArgumentsDoneEvent(
                call_id="call_id",
                arguments="argument delta",
                event_id="event_id",
                output_index=0,
                item_id="item_id",
                response_id="response_id",
                type="response.function_call_arguments.done",
            ),
            [RealtimeEvent],
            id="response_function_call_arguments_done_no_kernel",
        ),
        param(
            ErrorEvent(
                error={"code": "error_code", "message": "error_message", "type": "invalid_request_error"},
                event_id="event_id",
                type="error",
            ),
            [RealtimeEvent],
            id="error",
        ),
        param(
            SessionCreatedEvent(
                session=Session(id="session_id"),
                event_id="event_id",
                type="session.created",
            ),
            [RealtimeEvent],
            id="session_created",
        ),
        param(
            SessionUpdatedEvent(
                session=Session(id="session_id"),
                event_id="event_id",
                type="session.updated",
            ),
            [RealtimeEvent],
            id="session_updated",
        ),
        param(
            InputAudioBufferSpeechStartedEvent(
                audio_start_ms=0,
                event_id="event_id",
                item_id="item_id",
                type="input_audio_buffer.speech_started",
            ),
            [RealtimeEvent],
            id="other",
        ),
    ],
)
async def test_parse_event(OpenAIWebsocket, event: RealtimeServerEvent, expected_type: list[type]):
    iter = 0
    async for result in OpenAIWebsocket._parse_event(event):
        assert isinstance(result, expected_type[iter])
        iter += 1


async def test_update_session(OpenAIWebsocket, kernel):
    chat_history = ChatHistory(
        messages=[
            ChatMessageContent(role="user", content="Hello"),
            ChatMessageContent(
                role="assistant",
                items=[
                    FunctionCallContent(
                        function_name="function_name", plugin_name="plugin", arguments={"arg1": "value"}, id="1"
                    )
                ],
            ),
            ChatMessageContent(
                role="tool",
                items=[
                    FunctionResultContent(function_name="function_name", plugin_name="plugin", result="result", id="1")
                ],
            ),
            ChatMessageContent(
                role="user",
                items=[
                    TextContent(text="Hello again"),
                    ImageContent(uri="https://example.com/image.png"),
                ],
            ),
        ]
    )
    settings = OpenAIRealtimeExecutionSettings(instructions="instructions", ai_model_id="gpt-4o-realtime-preview")
    with patch.object(OpenAIWebsocket, "_send") as mock_send:
        await OpenAIWebsocket.update_session(
            chat_history=chat_history, settings=settings, create_response=True, kernel=kernel
        )
        mock_send.assert_awaited()
        # session update, 4 conversation item create events, response create
        # images are not supported, so ignored
        assert len(mock_send.await_args_list) == 6
    assert OpenAIWebsocket._current_settings == settings
    assert OpenAIWebsocket.kernel == kernel


async def test_parse_function_call_arguments_done(OpenAIWebsocket, kernel):
    func_result = "result"
    event = ResponseFunctionCallArgumentsDoneEvent(
        call_id="call_id",
        arguments='{"x": "' + func_result + '"}',
        event_id="event_id",
        output_index=0,
        item_id="item_id",
        response_id="response_id",
        type="response.function_call_arguments.done",
    )
    response_events = [RealtimeFunctionCallEvent, RealtimeFunctionResultEvent]
    OpenAIWebsocket._current_settings = OpenAIRealtimeExecutionSettings(
        instructions="instructions", ai_model_id="gpt-4o-realtime-preview"
    )
    OpenAIWebsocket._current_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    OpenAIWebsocket._call_id_to_function_map["call_id"] = "plugin_name-function_name"
    func = kernel_function(name="function_name", description="function_description")(lambda x: x)
    kernel.add_function(plugin_name="plugin_name", function_name="function_name", function=func)
    OpenAIWebsocket.kernel = kernel
    iter = 0
    with patch.object(OpenAIWebsocket, "_send") as mock_send:
        async for event in OpenAIWebsocket._parse_function_call_arguments_done(event):
            assert isinstance(event, response_events[iter])
            iter += 1
        mock_send.assert_awaited()
        assert len(mock_send.await_args_list) == 2
        mock_send.assert_any_await(
            ConversationItemCreateEvent(
                type="conversation.item.create",
                item=ConversationItem(
                    type="function_call_output",
                    output=func_result,
                    call_id="call_id",
                ),
            )
        )


async def test_parse_function_call_arguments_done_fail(OpenAIWebsocket, kernel):
    func_result = "result"
    event = ResponseFunctionCallArgumentsDoneEvent(
        call_id="call_id",
        arguments='{"x": "' + func_result + '"}',
        event_id="event_id",
        output_index=0,
        item_id="item_id",
        response_id="response_id",
        type="response.function_call_arguments.done",
    )
    response_events = [RealtimeEvent]
    OpenAIWebsocket._current_settings = OpenAIRealtimeExecutionSettings(
        instructions="instructions", ai_model_id="gpt-4o-realtime-preview"
    )
    OpenAIWebsocket._current_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
    # This function name is invalid
    OpenAIWebsocket._call_id_to_function_map["call_id"] = "function_name"
    func = kernel_function(name="function_name", description="function_description")(lambda x: x)
    kernel.add_function(plugin_name="plugin_name", function_name="function_name", function=func)
    OpenAIWebsocket.kernel = kernel
    iter = 0
    async for event in OpenAIWebsocket._parse_function_call_arguments_done(event):
        assert isinstance(event, response_events[iter])
        iter += 1


async def test_send_audio(OpenAIWebsocket):
    audio_event = RealtimeAudioEvent(
        audio=AudioContent(data=b"audio data", mime_type="audio/wav"),
    )
    with patch.object(OpenAIWebsocket, "_send") as mock_send:
        await OpenAIWebsocket.send(audio_event)
        mock_send.assert_awaited()
        assert len(mock_send.await_args_list) == 1
        mock_send.assert_any_await(
            InputAudioBufferAppendEvent(
                audio="audio data",
                type="input_audio_buffer.append",
            )
        )


@mark.parametrize("client", ["OpenAIWebRTC", "OpenAIWebsocket"])
async def test_send_session_update(client, OpenAIWebRTC, OpenAIWebsocket):
    openai_client = OpenAIWebRTC if client == "OpenAIWebRTC" else OpenAIWebsocket
    settings = PromptExecutionSettings(ai_model_id="gpt-4o-realtime-preview")
    session_event = RealtimeEvent(
        service_type=SendEvents.SESSION_UPDATE,
        service_event={"settings": settings},
    )
    with patch.object(openai_client, "_send") as mock_send:
        await openai_client.send(event=session_event)
        mock_send.assert_awaited()
        assert len(mock_send.await_args_list) == 1
        mock_send.assert_any_await(
            SessionUpdateEvent(
                session={"model": "gpt-4o-realtime-preview"},
                type="session.update",
            )
        )


@mark.parametrize("client", ["OpenAIWebRTC", "OpenAIWebsocket"])
async def test_send_conversation_item_create(client, OpenAIWebRTC, OpenAIWebsocket):
    openai_client = OpenAIWebRTC if client == "OpenAIWebRTC" else OpenAIWebsocket
    event = RealtimeEvent(
        service_type=SendEvents.CONVERSATION_ITEM_CREATE,
        service_event={
            "item": ChatMessageContent(
                role="user",
                items=[
                    TextContent(text="Hello"),
                    FunctionCallContent(
                        function_name="function_name",
                        plugin_name="plugin",
                        arguments={"arg1": "value"},
                        id="1",
                        metadata={"call_id": "call_id"},
                    ),
                    FunctionResultContent(
                        function_name="function_name",
                        plugin_name="plugin",
                        result="result",
                        id="1",
                        metadata={"call_id": "call_id"},
                    ),
                ],
            )
        },
    )

    with patch.object(openai_client, "_send") as mock_send:
        await openai_client.send(event=event)
        mock_send.assert_awaited()
        assert len(mock_send.await_args_list) == 3
        mock_send.assert_any_await(
            ConversationItemCreateEvent(
                item=ConversationItem(
                    content=[ConversationItemContent(text="Hello", type="input_text")],
                    role="user",
                    type="message",
                ),
                type="conversation.item.create",
            )
        )
        mock_send.assert_any_await(
            ConversationItemCreateEvent(
                item=ConversationItem(
                    arguments='{"arg1": "value"}',
                    call_id="call_id",
                    name="plugin-function_name",
                    type="function_call",
                ),
                type="conversation.item.create",
            )
        )
        mock_send.assert_any_await(
            ConversationItemCreateEvent(
                item=ConversationItem(
                    call_id="call_id",
                    output="result",
                    type="function_call_output",
                ),
                type="conversation.item.create",
            )
        )


async def test_receive_websocket(OpenAIWebsocket):
    connection_mock = AsyncMock(spec=AsyncRealtimeConnection)
    connection_mock.recv = websocket_stream

    manager = AsyncMock(spec=AsyncRealtimeConnectionManager)
    manager.enter.return_value = connection_mock

    with patch("openai.resources.beta.realtime.realtime.AsyncRealtime.connect") as mock_connect:
        mock_connect.return_value = manager
        async with OpenAIWebsocket():
            async for msg in OpenAIWebsocket.receive():
                assert isinstance(msg, RealtimeEvent)


async def test_receive_webrtc(OpenAIWebRTC):
    counter = len(events)
    with patch.object(OpenAIRealtimeWebRTC, "create_session"):
        recv_task = asyncio.create_task(_stream_to_webrtc(OpenAIWebRTC))
        async with OpenAIWebRTC():
            async for msg in OpenAIWebRTC.receive():
                assert isinstance(msg, RealtimeEvent)
                counter -= 1
                if counter == 0:
                    break
        recv_task.cancel()


async def _stream_to_webrtc(client: OpenAIRealtimeWebRTC):
    async for msg in websocket_stream():
        async for parsed_msg in client._parse_event(msg):
            await client._receive_buffer.put(parsed_msg)
            await asyncio.sleep(0)


# @pytest.fixture
# async def openai_realtime_base():
#     kernel_mock = AsyncMock(Kernel)
#     obj = OpenAIRealtimeWebRTC(audio_track=AsyncMock(), client=AsyncMock(), ai_model_id="gpt-3", kernel=kernel_mock)
#     return obj


# @pytest.fixture
# async def prepare_event():
#     def _prepare_event(event_type, **kwargs):
#         return RealtimeEvent(service_event=kwargs, service_type=event_type)

#     return _prepare_event


# @pytest.mark.asyncio
# async def test_initialization(openai_realtime_base):
#     """Test to verify proper creation and defaults settings initialization of OpenAIRealtimeWebRTC."""
#     assert openai_realtime_base.SUPPORTS_FUNCTION_CALLING is True
#     assert openai_realtime_base.kernel is not None


# @pytest.mark.asyncio
# async def test_send_method(openai_realtime_base):
#     """Test to ensure send method delegates to _send method correctly."""

#     # Mock _send method
#     openai_realtime_base._send = AsyncMock()

#     # Create a RealtimeTextEvent
#     text_event = RealtimeTextEvent(service_type=SendEvents.CONVERSATION_ITEM_CREATE, text=TextContent(text="Hello"))

#     # Call the send method
#     await openai_realtime_base.send(text_event)

#     # Assert _send was called correctly
#     openai_realtime_base._send.assert_awaited_once_with(
#         RealtimeTextEvent(service_type=SendEvents.CONVERSATION_ITEM_CREATE, text=TextContent(text="Hello"))
#     )


# @pytest.mark.asyncio
# async def test_update_session_with_no_kernel(prepare_event):
#     """Test update_session without kernel argument provided and with PromptExecutionSettings."""

#     # Mocks
#     mock_settings = Mock(spec=PromptExecutionSettings)

#     # Setup OpenAIRealtimeWebRTC instance
#     base = OpenAIRealtimeWebRTC(audio_track=AsyncMock(), client=AsyncMock(), ai_model_id="gpt-3")

#     # Call update_session
#     await base.update_session(settings=mock_settings, create_response=True)

#     # Assertions
#     assert base.kernel is None
#     assert base._current_settings is mock_settings


# @pytest.mark.asyncio
# @patch("semantic_kernel.connectors.ai.function_calling_utils.prepare_settings_for_function_calling")
# async def test_update_session_with_kernel(mocked_prepare, openai_realtime_base, prepare_event):
#     """Test update_session updates with kernel and PromptExecutionSettings."""

#     # Mocks
#     mock_settings = PromptExecutionSettings(service_id="test")

#     # Call update_session
#     await openai_realtime_base.update_session(settings=mock_settings, kernel=openai_realtime_base.kernel)

#     # Ensure kernel-related processes are executed
#     mocked_prepare.assert_called_once_with(
#         mock_settings,
#         openai_realtime_base.get_prompt_execution_settings_class(),
#         openai_realtime_base._update_function_choice_settings_callback(),
#         kernel=openai_realtime_base.kernel,
#     )


# @pytest.mark.asyncio
# async def test_handle_audio_transcript_delta(openai_realtime_base, prepare_event):
#     """Test to ensure audio transcript delta is handled correctly."""

#     # Mock asyncio.Queue to check data passed to buffer
#     openai_realtime_base._receive_buffer = AsyncMock()

#     # Prepare a sample audio transcript event
#     sample_event = prepare_event(ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value, delta="text")

#     async for event in openai_realtime_base._parse_event(sample_event):
#         assert isinstance(event, RealtimeTextEvent)

#     # Check if item put in the buffer
#     openai_realtime_base._receive_buffer.put.assert_awaited()


# @pytest.mark.asyncio
# async def test_parse_function_call_arguments_done(openai_realtime_base):
#     """Test parsing and execution of function call arguments done."""

#     # Prepare mock data
#     call_event = ResponseFunctionCallArgumentsDoneEvent(
#         type=ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE.value,
#         call_id="sample-id",
#         item_id="1234",
#         arguments='{"param": "value"}',
#     )

#     # Create chat history mock
#     mock_chat_history = AsyncMock(ChatHistory)
#     openai_realtime_base.kernel.invoke_function_call = AsyncMock()

#     # Call the function
#     async for event in openai_realtime_base._parse_function_call_arguments_done(call_event):
#         pass

#     # Ensure correct method is called in kernel
#     openai_realtime_base.kernel.invoke_function_call.assert_called_with(
#         FunctionCallContent(id="1234", plugin_name="", function_name="sample-id", arguments='{"param": "value"}'),
#         mock_chat_history,
#     )


# @pytest.mark.asyncio
# async def test_handle_unknown_event_type(openai_realtime_base, prepare_event):
#     """Test handling of an unknown/unexpected event type."""

#     # Prepare a sample unknown event
#     unknown_event = prepare_event("unknown:event")

#     # Mock put method
#     openai_realtime_base._receive_buffer.put = AsyncMock()

#     async for event in openai_realtime_base._parse_event(unknown_event):
#         # The event should still be added to the buffer
#         openai_realtime_base._receive_buffer.put.assert_awaited_with(event)


# @pytest.mark.asyncio
# async def test_close_session(openai_realtime_base):
#     """Test session close functionality."""
#     # Mock close method of peer connection and data channel
#     if openai_realtime_base.peer_connection:
#         openai_realtime_base.peer_connection.close = AsyncMock()
#     if openai_realtime_base.data_channel:
#         openai_realtime_base.data_channel.close = AsyncMock()

#     # Call close_session and verify
#     await openai_realtime_base.close_session()
#     if openai_realtime_base.peer_connection:
#         openai_realtime_base.peer_connection.close.assert_awaited_once()
#     if openai_realtime_base.data_channel:
#         openai_realtime_base.data_channel.close.assert_awaited_once()
