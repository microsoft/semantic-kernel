# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Any
from unittest.mock import patch

from aiortc import AudioStreamTrack
from openai.types.beta.realtime import (
    ConversationItem,
    ConversationItemCreatedEvent,
    ConversationItemCreateEvent,
    ConversationItemDeletedEvent,
    ConversationItemDeleteEvent,
    ConversationItemTruncatedEvent,
    ConversationItemTruncateEvent,
    ErrorEvent,
    InputAudioBufferAppendEvent,
    InputAudioBufferClearEvent,
    InputAudioBufferCommitEvent,
    InputAudioBufferSpeechStartedEvent,
    RealtimeServerEvent,
    ResponseAudioDeltaEvent,
    ResponseAudioDoneEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseCancelEvent,
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


@fixture
async def websocket_stream():
    await asyncio.sleep(0)
    yield SessionCreatedEvent(type=ListenEvents.SESSION_CREATED, session=Session(session_id="session_id"), event_id="1")
    yield SessionUpdatedEvent(type=ListenEvents.SESSION_UPDATED, session=Session(session_id="session_id"), event_id="2")
    yield ConversationItemCreatedEvent(
        type=ListenEvents.CONVERSATION_ITEM_CREATED,
        item=ConversationItem(id="item_id"),
        event_id="3",
        previous_item_id="2",
    )
    yield ConversationItemDeletedEvent(type=ListenEvents.CONVERSATION_ITEM_DELETED, item_id="item_id", event_id="4")
    yield ConversationItemTruncatedEvent(type=ListenEvents.CONVERSATION_ITEM_TRUNCATED, event_id="5")
    yield InputAudioBufferClearEvent(type=ListenEvents.INPUT_AUDIO_BUFFER_CLEARED, event_id="7")
    yield InputAudioBufferCommitEvent(type=ListenEvents.INPUT_AUDIO_BUFFER_COMMITTED, event_id="8")
    yield ResponseCancelEvent(type=ListenEvents.RESPONSE_CANCELLED, event_id="9")
    yield ResponseCreateEvent(type=ListenEvents.RESPONSE_CREATED, event_id="10")
    yield ResponseFunctionCallArgumentsDoneEvent(type=ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE, event_id="11")
    yield ResponseAudioTranscriptDeltaEvent(type=ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA, event_id="12")
    yield ResponseAudioDoneEvent(type=ListenEvents.RESPONSE_AUDIO_DONE, event_id="13")
    yield ResponseAudioDeltaEvent(type=ListenEvents.RESPONSE_AUDIO_DELTA, event_id="14")


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
