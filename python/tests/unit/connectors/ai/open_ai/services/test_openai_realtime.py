# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Any

from aiortc import AudioStreamTrack
from openai.types.beta.realtime import (
    ConversationItem,
    ConversationItemCreatedEvent,
    ConversationItemCreateEvent,
    ConversationItemDeletedEvent,
    ConversationItemDeleteEvent,
    ConversationItemTruncatedEvent,
    ConversationItemTruncateEvent,
    InputAudioBufferAppendEvent,
    InputAudioBufferClearEvent,
    InputAudioBufferCommitEvent,
    ResponseAudioDeltaEvent,
    ResponseAudioDoneEvent,
    ResponseAudioTranscriptDeltaEvent,
    ResponseCancelEvent,
    ResponseCreateEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    Session,
    SessionCreatedEvent,
    SessionUpdatedEvent,
    SessionUpdateEvent,
)
from pytest import fixture, mark, param, raises

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
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
from semantic_kernel.exceptions.content_exceptions import ContentException
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
