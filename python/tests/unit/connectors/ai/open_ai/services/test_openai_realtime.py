# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import AsyncIterable
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aiortc import AudioStreamTrack, RTCDataChannel, RTCPeerConnection
from numpy import ndarray
from openai import AsyncOpenAI
from openai.resources.beta.realtime.realtime import (
    AsyncRealtimeConnection,
    AsyncRealtimeConnectionManager,
)
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
from pydantic import ValidationError
from pytest import fixture, mark, param, raises

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    OpenAIRealtimeExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime import (
    ListenEvents,
    SendEvents,
    _create_openai_realtime_client_event,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_realtime import (
    OpenAIRealtimeWebRTC,
    OpenAIRealtimeWebsocket,
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
from semantic_kernel.kernel import Kernel

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
    assert OpenAIWebsocket._kernel == kernel


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
    OpenAIWebsocket._kernel = kernel
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


@pytest.fixture
async def openai_realtime_base():
    kernel_mock = AsyncMock(spec=Kernel)
    async_openai_mock = AsyncMock(spec=AsyncOpenAI)
    audio_track_mock = AsyncMock(spec=AudioStreamTrack)
    return OpenAIRealtimeWebRTC(
        audio_track=audio_track_mock,
        client=async_openai_mock,
        ai_model_id="gpt-4o-realtime-preview",
        kernel=kernel_mock,
    )


@pytest.fixture
async def prepare_event():
    def _prepare_event(**kwargs):
        return ResponseAudioTranscriptDeltaEvent(**kwargs)

    return _prepare_event


async def test_initialization(openai_realtime_base):
    """Test to verify proper creation and defaults settings initialization of OpenAIRealtimeWebRTC."""
    assert openai_realtime_base.SUPPORTS_FUNCTION_CALLING is True
    assert openai_realtime_base.kernel is not None


async def test_send_method(openai_realtime_base):
    """Test to ensure send method delegates to _send method correctly."""

    openai_realtime_base._send = AsyncMock()
    text_event = RealtimeTextEvent(service_type=SendEvents.CONVERSATION_ITEM_CREATE, text=TextContent(text="Hello"))
    await openai_realtime_base.send(text_event)
    openai_realtime_base._send.assert_awaited_once()


async def test_update_session_with_no_kernel():
    """Test update_session without kernel argument provided and with PromptExecutionSettings."""

    async_openai_mock = AsyncMock(spec=AsyncOpenAI)
    audio_track_mock = AsyncMock(spec=AudioStreamTrack)
    mock_settings = AsyncMock(spec=PromptExecutionSettings)

    base = OpenAIRealtimeWebRTC(audio_track=audio_track_mock, client=async_openai_mock, ai_model_id="gpt-3")

    await base.update_session(settings=mock_settings, create_response=True)

    assert not hasattr(base, "kernel")
    assert base._current_settings is mock_settings


async def test_update_session_with_kernel(openai_realtime_base):
    """Test update_session updates with kernel and PromptExecutionSettings."""
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services._open_ai_realtime.prepare_settings_for_function_calling",
    ) as mocked_prepare:
        settings = PromptExecutionSettings(service_id="test")

        await openai_realtime_base.update_session(settings=settings, kernel=openai_realtime_base.kernel)

        # Ensure kernel-related processes are executed
        mocked_prepare.assert_called_once_with(
            settings,
            openai_realtime_base.get_prompt_execution_settings_class(),
            openai_realtime_base._update_function_choice_settings_callback(),
            kernel=openai_realtime_base.kernel,
        )


async def test_handle_audio_transcript_delta(openai_realtime_base, prepare_event):
    """Test to ensure audio transcript delta is handled correctly."""

    openai_realtime_base._receive_buffer = AsyncMock()

    # Prepare a sample audio transcript event
    sample_event = prepare_event(
        type=ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value,
        delta="text",
        content_index=0,
        item_id="item_id",
        output_index=0,
        response_id="response_id",
        event_id="event_id",
    )

    async for event in openai_realtime_base._parse_event(sample_event):
        assert event.event_type == "text"


async def test_handle_unknown_event_type(prepare_event):
    """Test handling of an unknown/unexpected event type."""

    with pytest.raises(ValidationError):
        # Prepare a sample unknown event
        prepare_event(
            type="unknown:event",
            delta="text",
            content_index=0,
            item_id="item_id",
            output_index=0,
            response_id="response_id",
            event_id="event_id",
        )


async def test_close_session(openai_realtime_base):
    """Test session close functionality."""
    # Mock close method of peer connection and data channel
    if openai_realtime_base.peer_connection:
        openai_realtime_base.peer_connection.close = AsyncMock()
    if openai_realtime_base.data_channel:
        openai_realtime_base.data_channel.close = AsyncMock()

    # Call close_session and verify
    await openai_realtime_base.close_session()
    if openai_realtime_base.peer_connection:
        openai_realtime_base.peer_connection.close.assert_awaited_once()
    if openai_realtime_base.data_channel:
        openai_realtime_base.data_channel.close.assert_awaited_once()


@pytest.fixture
def mocked_audio_track():
    """Fixture for creating a mocked MediaStreamTrack object."""
    mocked_audio_track = AsyncMock(name="AudioStreamTrack", spec=AudioStreamTrack)
    mocked_audio_track.kind = "audio"
    return mocked_audio_track


@pytest.fixture
def mocked_audio_output_callback():
    """Fixture for creating a mocked audio output callback."""
    return AsyncMock(name="audio_output_callback")


@pytest.fixture
def mocked_open_ai_realtime_webrtc(mocked_audio_track, mocked_audio_output_callback):
    """Fixture for initializing the OpenAIRealtimeWebRTC with mocked components."""
    async_openai_mock = AsyncMock(spec=AsyncOpenAI)

    with patch("aiohttp.ClientSession", autospec=True):
        return OpenAIRealtimeWebRTC(
            audio_track=mocked_audio_track,
            audio_output_callback=mocked_audio_output_callback,
            ai_model_id="gpt-4o-realtime-preview",
            client=async_openai_mock,
            api_key="fake-api-key",
        )


@patch("aiohttp.ClientSession.post")
async def test_create_session_initializes_peer_connection(mock_post, mocked_open_ai_realtime_webrtc):
    """Test the create_session method to ensure peer connection initializes correctly."""

    mock_post.return_value.__aenter__.return_value.text = AsyncMock(
        return_value=(
            "v=0\r\n"
            "o=- 3952301147 3952301147 IN IP4 0.0.0.0\r\n"
            "s=-\r\n"
            "t=0 0\r\n"
            "a=group:BUNDLE 0 1\r\n"
            "a=msid-semantic:WMS *\r\n"
            "m=audio 9 UDP/TLS/RTP/SAVPF 96 0 8\r\n"
            "c=IN IP4 0.0.0.0\r\n"
            "a=sendrecv\r\n"
            "a=extmap:1 urn:ietf:params:rtp-hdrext:sdes:mid\r\n"
            "a=extmap:2 urn:ietf:params:rtp-hdrext:ssrc-audio-level\r\n"
            "a=mid:0\r\n"
            "a=msid:cb09f50e-e695-4288-8d75-cb65cdbc1416 "
            "<MagicMock name='AudioStreamTrack.id' id='13114266080'>\r\n"
            "a=rtcp:9 IN IP4 0.0.0.0\r\n"
            "a=rtcp-mux\r\n"
            "a=ssrc:1360920249 cname:bc7cf41e-0974-42a4-a47f-a7b3d7f19370\r\n"
            "a=rtpmap:96 opus/48000/2\r\n"
            "a=rtpmap:0 PCMU/8000\r\n"
            "a=rtpmap:8 PCMA/8000\r\n"
            "a=ice-ufrag:LZOR\r\n"
            "a=ice-pwd:puTRy8Rdc9btpLEGh8pQ40\r\n"
            "a=fingerprint:sha-256 "
            "9C:E7:82:2E:D0:82:56:ED:EE:45:41:8B:6D:55:01:F2:67:48:C4:51:D1:2C:E8:55:F7:21:0B:85:E2:39:32:63\r\n"
            "a=fingerprint:sha-384 "
            "C3:96:0F:4C:2F:92:53:8D:37:AB:4E:B7:E1:A4:CF:DE:2E:88:45:8E:EC:0D:67:CA:36:7F:CA:AC:CF:77:70:69:71:8F:1D:86:"
            "58:71:A4:3D:2E:01:61:E9:55:87:61:F9\r\n"
            "a=fingerprint:sha-512 "
            "59:C9:62:0B:A9:6A:A2:51:1B:D4:FD:64:AA:EB:F0:4B:F0:3B:A9:63:1E:CF:...\r\n"
            "a=setup:active\r\n"
            "m=application 9 DTLS/SCTP 5000\r\n"
            "c=IN IP4 0.0.0.0\r\n"
            "a=mid:1\r\n"
            "a=sctpmap:5000 webrtc-datachannel 65535\r\n"
            "a=max-message-size:65536\r\n"
            "a=ice-ufrag:X8yT\r\n"
            "a=ice-pwd:9XkLRk2g1mLvKPscP8J4hY\r\n"
            "a=fingerprint:sha-256 "
            "9C:E7:82:2E:D0:82:56:ED:EE:45:41:8B:6D:55:01:F2:67:48:C4:51:D1:2C:E8:55:F7:21:0B:85:E2:39:32:63\r\n"
            "a=setup:active\r\n"
        )
    )

    mock_post.return_value.__aenter__.return_value.status = 200

    mocked_open_ai_realtime_webrtc._get_ephemeral_token = AsyncMock(return_value="fake-token")
    mocked_open_ai_realtime_webrtc.client = AsyncMock(spec=AsyncOpenAI)
    mocked_open_ai_realtime_webrtc.client.api_key = "fake-api-key"
    mocked_open_ai_realtime_webrtc.client.beta = AsyncMock()
    mocked_open_ai_realtime_webrtc.client.beta.realtime = AsyncMock()
    mocked_open_ai_realtime_webrtc.client.beta.realtime._client = AsyncMock()
    mocked_open_ai_realtime_webrtc.client.beta.realtime._client.base_url = "https://api.openai.com"

    await mocked_open_ai_realtime_webrtc.create_session()
    assert mocked_open_ai_realtime_webrtc.peer_connection is not None
    assert mocked_open_ai_realtime_webrtc.data_channel is not None


async def test_create_session_fails_without_audio_track(mocked_audio_output_callback):
    """Test the create_session method raises an exception when audio track is uninitialized."""
    async_openai_mock = AsyncMock(spec=AsyncOpenAI)

    webrtc_instance = OpenAIRealtimeWebRTC(
        audio_track=None,
        audio_output_callback=mocked_audio_output_callback,
        client=async_openai_mock,
        ai_model_id="fake-model-id",
    )

    with pytest.raises(Exception, match="Audio track not initialized"):
        await webrtc_instance.create_session()


async def test_receive_yields_realtime_events(mocked_open_ai_realtime_webrtc, mocked_audio_output_callback):
    """Ensure the receive function properly yields RealtimeEvents."""
    mocked_realtime_event = AsyncMock(ndarray)
    mocked_open_ai_realtime_webrtc._receive_buffer.put_nowait(mocked_realtime_event)

    event_generator = mocked_open_ai_realtime_webrtc.receive(mocked_audio_output_callback)
    event = await event_generator.asend(None)

    assert event is mocked_realtime_event


async def test_close_session_terminates_connections(mocked_open_ai_realtime_webrtc):
    """Test that close_session properly closes peer connection and data channel."""
    mocked_open_ai_realtime_webrtc.peer_connection = AsyncMock(spec=RTCPeerConnection)
    mocked_open_ai_realtime_webrtc.data_channel = AsyncMock(spec=RTCDataChannel)

    await mocked_open_ai_realtime_webrtc.close_session()

    assert mocked_open_ai_realtime_webrtc.peer_connection is None
    assert mocked_open_ai_realtime_webrtc.data_channel is None
