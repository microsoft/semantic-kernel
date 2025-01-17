# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import contextlib
import json
import logging
import sys
from collections.abc import AsyncGenerator, Callable, Coroutine
from enum import Enum
from inspect import isawaitable
from typing import Any, ClassVar, Protocol, cast, runtime_checkable

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from aiohttp import ClientSession
from aiortc import (
    MediaStreamTrack,
    RTCConfiguration,
    RTCDataChannel,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from av import AudioFrame
from openai._models import construct_type_unchecked
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from openai.types.beta.realtime.conversation_item_create_event_param import ConversationItemParam
from openai.types.beta.realtime.realtime_server_event import RealtimeServerEvent
from pydantic import Field, PrivateAttr

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import (
    prepare_settings_for_function_calling,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.open_ai_realtime_utils import (
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.connectors.ai.realtime_helpers import SKAudioTrack
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)

# region Protocols


@runtime_checkable
@experimental_class
class EventCallBackProtocolAsync(Protocol):
    """Event callback protocol."""

    async def __call__(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool] | None:
        """Call the event callback."""
        ...


@runtime_checkable
@experimental_class
class EventCallBackProtocol(Protocol):
    """Event callback protocol."""

    def __call__(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool] | None:
        """Call the event callback."""
        ...


# region Events


@experimental_class
class SendEvents(str, Enum):
    """Events that can be sent."""

    SESSION_UPDATE = "session.update"
    INPUT_AUDIO_BUFFER_APPEND = "input_audio_buffer.append"
    INPUT_AUDIO_BUFFER_COMMIT = "input_audio_buffer.commit"
    INPUT_AUDIO_BUFFER_CLEAR = "input_audio_buffer.clear"
    CONVERSATION_ITEM_CREATE = "conversation.item.create"
    CONVERSATION_ITEM_TRUNCATE = "conversation.item.truncate"
    CONVERSATION_ITEM_DELETE = "conversation.item.delete"
    RESPONSE_CREATE = "response.create"
    RESPONSE_CANCEL = "response.cancel"


@experimental_class
class ListenEvents(str, Enum):
    """Events that can be listened to."""

    ERROR = "error"
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    CONVERSATION_CREATED = "conversation.created"
    INPUT_AUDIO_BUFFER_COMMITTED = "input_audio_buffer.committed"
    INPUT_AUDIO_BUFFER_CLEARED = "input_audio_buffer.cleared"
    INPUT_AUDIO_BUFFER_SPEECH_STARTED = "input_audio_buffer.speech_started"
    INPUT_AUDIO_BUFFER_SPEECH_STOPPED = "input_audio_buffer.speech_stopped"
    CONVERSATION_ITEM_CREATED = "conversation.item.created"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED = "conversation.item.input_audio_transcription.completed"
    CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_FAILED = "conversation.item.input_audio_transcription.failed"
    CONVERSATION_ITEM_TRUNCATED = "conversation.item.truncated"
    CONVERSATION_ITEM_DELETED = "conversation.item.deleted"
    RESPONSE_CREATED = "response.created"
    RESPONSE_DONE = "response.done"  # contains usage info -> log
    RESPONSE_OUTPUT_ITEM_ADDED = "response.output_item.added"
    RESPONSE_OUTPUT_ITEM_DONE = "response.output_item.done"
    RESPONSE_CONTENT_PART_ADDED = "response.content_part.added"
    RESPONSE_CONTENT_PART_DONE = "response.content_part.done"
    RESPONSE_TEXT_DELTA = "response.text.delta"
    RESPONSE_TEXT_DONE = "response.text.done"
    RESPONSE_AUDIO_TRANSCRIPT_DELTA = "response.audio_transcript.delta"
    RESPONSE_AUDIO_TRANSCRIPT_DONE = "response.audio_transcript.done"
    RESPONSE_AUDIO_DELTA = "response.audio.delta"
    RESPONSE_AUDIO_DONE = "response.audio.done"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA = "response.function_call_arguments.delta"
    RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE = "response.function_call_arguments.done"
    RATE_LIMITS_UPDATED = "rate_limits.updated"


# region Websocket


@experimental_class
class OpenAIRealtimeBase(OpenAIHandler, RealtimeClientBase):
    """OpenAI Realtime service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True
    connection: AsyncRealtimeConnection | None = None
    connected: asyncio.Event = Field(default_factory=asyncio.Event)
    event_log: dict[str, list[RealtimeServerEvent]] = Field(default_factory=dict)
    event_handlers: dict[str, list[EventCallBackProtocol | EventCallBackProtocolAsync]] = Field(default_factory=dict)

    def model_post_init(self, *args, **kwargs) -> None:
        """Post init method for the model."""
        # Register the default event handlers
        self.register_event_handler(ListenEvents.RESPONSE_AUDIO_DELTA, self.response_audio_delta_callback)
        self.register_event_handler(
            ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA, self.response_audio_transcript_delta_callback
        )
        self.register_event_handler(
            ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DONE, self.response_audio_transcript_done_callback
        )
        self.register_event_handler(
            ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE, self.response_function_call_arguments_delta_callback
        )
        self.register_event_handler(ListenEvents.ERROR, self.error_callback)
        self.register_event_handler(ListenEvents.SESSION_CREATED, self.session_callback)
        self.register_event_handler(ListenEvents.SESSION_UPDATED, self.session_callback)

    def register_event_handler(
        self, event_type: str | ListenEvents, handler: EventCallBackProtocol | EventCallBackProtocolAsync
    ) -> None:
        """Register a event handler."""
        if not isinstance(event_type, ListenEvents):
            event_type = ListenEvents(event_type)
        self.event_handlers.setdefault(event_type, []).append(handler)

    @override
    async def start_listening(
        self,
        settings: "PromptExecutionSettings",
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamingChatMessageContent, Any]:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection is not established.")
        if not chat_history:
            chat_history = ChatHistory()
        async for event in self.connection:
            event_type = ListenEvents(event.type)
            self.event_log.setdefault(event_type, []).append(event)
            for handler in self.event_handlers.get(event_type, []):
                task = handler(event=event, settings=settings)
                if not task:
                    continue
                if isawaitable(task):
                    async_result = await task
                    if not async_result:
                        continue
                    result, should_return = async_result
                else:
                    result, should_return = task
                if should_return:
                    yield result
                else:
                    chat_history.add_message(result)

        for event_type in self.event_log:
            logger.debug(f"Event type: {event_type}, count: {len(self.event_log[event_type])}")

    @override
    async def start_sending(self, event: str | SendEvents, **kwargs: Any) -> None:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection is not established.")
        if not isinstance(event, SendEvents):
            event = SendEvents(event)
        match event:
            case SendEvents.SESSION_UPDATE:
                if "settings" not in kwargs:
                    logger.error("Event data does not contain 'settings'")
                await self.connection.session.update(session=kwargs["settings"].prepare_settings_dict())
            case SendEvents.INPUT_AUDIO_BUFFER_APPEND:
                if "content" not in kwargs:
                    logger.error("Event data does not contain 'content'")
                    return
                await self.connection.input_audio_buffer.append(audio=kwargs["content"].data.decode("utf-8"))
            case SendEvents.INPUT_AUDIO_BUFFER_COMMIT:
                await self.connection.input_audio_buffer.commit()
            case SendEvents.INPUT_AUDIO_BUFFER_CLEAR:
                await self.connection.input_audio_buffer.clear()
            case SendEvents.CONVERSATION_ITEM_CREATE:
                if "item" not in kwargs:
                    logger.error("Event data does not contain 'item'")
                    return
                content = kwargs["item"]
                for item in content.items:
                    match item:
                        case TextContent():
                            await self.connection.conversation.item.create(
                                item=ConversationItemParam(
                                    type="message",
                                    content=[
                                        {
                                            "type": "input_text",
                                            "text": item.text,
                                        }
                                    ],
                                    role="user",
                                )
                            )
                        case FunctionCallContent():
                            call_id = item.metadata.get("call_id")
                            if not call_id:
                                logger.error("Function call needs to have a call_id")
                                continue
                            await self.connection.conversation.item.create(
                                item=ConversationItemParam(
                                    type="function_call",
                                    name=item.name,
                                    arguments=item.arguments,
                                    call_id=call_id,
                                )
                            )
                        case FunctionResultContent():
                            call_id = item.metadata.get("call_id")
                            if not call_id:
                                logger.error("Function result needs to have a call_id")
                                continue
                            await self.connection.conversation.item.create(
                                item=ConversationItemParam(
                                    type="function_call_output",
                                    output=item.result,
                                    call_id=call_id,
                                )
                            )
            case SendEvents.CONVERSATION_ITEM_TRUNCATE:
                if "item_id" not in kwargs:
                    logger.error("Event data does not contain 'item_id'")
                    return
                await self.connection.conversation.item.truncate(
                    item_id=kwargs["item_id"], content_index=0, audio_end_ms=kwargs.get("audio_end_ms", 0)
                )
            case SendEvents.CONVERSATION_ITEM_DELETE:
                if "item_id" not in kwargs:
                    logger.error("Event data does not contain 'item_id'")
                    return
                await self.connection.conversation.item.delete(item_id=kwargs["item_id"])
            case SendEvents.RESPONSE_CREATE:
                if "response" in kwargs:
                    await self.connection.response.create(response=kwargs["response"])
                else:
                    await self.connection.response.create()
            case SendEvents.RESPONSE_CANCEL:
                if "response_id" in kwargs:
                    await self.connection.response.cancel(response_id=kwargs["response_id"])
                else:
                    await self.connection.response.cancel()

    @override
    async def create_session(
        self,
        settings: PromptExecutionSettings | None = None,
        chat_history: ChatHistory | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a session in the service."""
        self.connection = await self.client.beta.realtime.connect(model=self.ai_model_id).enter()
        self.connected.set()
        if settings or chat_history or kwargs:
            await self.update_session(settings=settings, chat_history=chat_history, **kwargs)

    @override
    async def update_session(
        self, settings: PromptExecutionSettings | None = None, chat_history: ChatHistory | None = None, **kwargs: Any
    ) -> None:
        if settings:
            if "kernel" in kwargs:
                settings = prepare_settings_for_function_calling(
                    settings,
                    self.get_prompt_execution_settings_class(),
                    self._update_function_choice_settings_callback(),
                    kernel=kwargs.get("kernel"),  # type: ignore
                )
            await self.start_sending(SendEvents.SESSION_UPDATE, settings=settings)
        if chat_history and len(chat_history) > 0:
            await asyncio.gather(
                *(self.start_sending(SendEvents.CONVERSATION_ITEM_CREATE, item=msg) for msg in chat_history.messages)
            )

    @override
    async def close_session(self) -> None:
        """Close the session in the service."""
        if self.connected.is_set():
            await self.connection.close()
            self.connection = None
            self.connected.clear()

    # region Event callbacks

    def response_audio_delta_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool]:
        """Handle response audio delta."""
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[AudioContent(data=base64.b64decode(event.delta), data_format="base64")],
            choice_index=event.content_index,
            inner_content=event,
        ), True

    def response_audio_transcript_delta_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool]:
        """Handle response audio transcript delta."""
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[StreamingTextContent(text=event.delta, choice_index=event.content_index)],
            choice_index=event.content_index,
            inner_content=event,
        ), True

    def response_audio_transcript_done_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool]:
        """Handle response audio transcript done."""
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[StreamingTextContent(text=event.transcript, choice_index=event.content_index)],
            choice_index=event.content_index,
            inner_content=event,
        ), False

    def response_function_call_arguments_delta_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> tuple[Any, bool]:
        """Handle response function call arguments delta."""
        return StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[
                FunctionCallContent(
                    id=event.item_id,
                    name=event.call_id,
                    arguments=event.delta,
                    index=event.output_index,
                    metadata={"call_id": event.call_id},
                )
            ],
            choice_index=0,
            inner_content=event,
        ), True

    def error_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle error."""
        logger.error("Error received: %s", event.error)

    def session_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle session."""
        logger.debug("Session created or updated, session: %s", event.session)

    async def response_function_call_arguments_done_callback(
        self,
        event: RealtimeServerEvent,
        settings: PromptExecutionSettings | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle response function call done."""
        item = FunctionCallContent(
            id=event.item_id,
            name=event.call_id,
            arguments=event.delta,
            index=event.output_index,
            metadata={"call_id": event.call_id},
        )
        kernel: Kernel | None = kwargs.get("kernel")
        call_id = item.name
        function_name = next(
            output_item_event.item.name
            for output_item_event in self.event_log[ListenEvents.RESPONSE_OUTPUT_ITEM_ADDED]
            if output_item_event.item.call_id == call_id
        )
        item.plugin_name, item.function_name = function_name.split("-", 1)
        if kernel:
            chat_history = ChatHistory()
            await kernel.invoke_function_call(item, chat_history)
            await self.start_sending(SendEvents.CONVERSATION_ITEM_CREATE, item=chat_history.messages[-1])
            # The model doesn't start responding to the tool call automatically, so triggering it here.
            await self.start_sending(SendEvents.RESPONSE_CREATE)
        return chat_history.messages[-1], False

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (  # noqa
            OpenAIRealtimeExecutionSettings,
        )

        return OpenAIRealtimeExecutionSettings


# region WebRTC


@experimental_class
class OpenAIRealtimeWebRTCBase(OpenAIHandler, RealtimeClientBase):
    """OpenAI WebRTC Realtime service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True
    peer_connection: RTCPeerConnection | None = None
    data_channel: RTCDataChannel | None = None
    audio_output: Callable[[AudioFrame], Coroutine[Any, Any, None] | None] | None = None
    kernel: Kernel | None = None

    _current_settings: PromptExecutionSettings | None = PrivateAttr(None)
    _call_id_to_function_map: dict[str, str] = PrivateAttr(default_factory=dict)

    @override
    async def start_listening(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        **kwargs: Any,
    ) -> None:
        pass

    async def _on_track(self, track: MediaStreamTrack) -> None:
        logger.info(f"Received {track.kind} track from remote")
        if track.kind != "audio":
            return
        while True:
            try:
                # This is a MediaStreamTrack, so the type is AudioFrame
                # this might need to be updated if video becomes part of this
                frame: AudioFrame = await track.recv()  # type: ignore
            except Exception as e:
                logger.error(f"Error getting audio frame: {e!s}")
                break

            try:
                if self.audio_output:
                    out = self.audio_output(frame)
                    if isawaitable(out):
                        await out

            except Exception as e:
                logger.error(f"Error playing remote audio frame: {e!s}")
            try:
                await self.receive_buffer.put(
                    (
                        ListenEvents.RESPONSE_AUDIO_DELTA,
                        StreamingChatMessageContent(
                            role=AuthorRole.ASSISTANT,
                            items=[AudioContent(data=frame.to_ndarray(), data_format="np.int16", inner_content=frame)],  # type: ignore
                            choice_index=0,
                        ),
                    ),
                )
            except Exception as e:
                logger.error(f"Error processing remote audio frame: {e!s}")
            await asyncio.sleep(0.01)

    async def _on_data(self, data: str) -> None:
        """This method is called whenever a data channel message is received.

        The data is parsed into a RealtimeServerEvent (by OpenAI) and then processed.
        """
        try:
            event = cast(
                RealtimeServerEvent,
                construct_type_unchecked(value=json.loads(data), type_=cast(Any, RealtimeServerEvent)),
            )
        except Exception as e:
            logger.error(f"Failed to parse event {data} with error: {e!s}")
            return
        match event.type:
            case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA:
                await self.receive_buffer.put((
                    event.type,
                    StreamingChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content=event.delta,
                        choice_index=event.content_index,
                        inner_content=event,
                    ),
                ))
            case ListenEvents.RESPONSE_OUTPUT_ITEM_ADDED:
                if event.item.type == "function_call":
                    self._call_id_to_function_map[event.item.call_id] = event.item.name
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA:
                await self.receive_buffer.put((
                    event.type,
                    StreamingChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        items=[
                            FunctionCallContent(
                                id=event.item_id,
                                name=event.call_id,
                                arguments=event.delta,
                                index=event.output_index,
                                metadata={"call_id": event.call_id},
                            )
                        ],
                        choice_index=0,
                        inner_content=event,
                    ),
                ))
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE:
                await self._handle_function_call_arguments_done(event)
            case ListenEvents.ERROR:
                logger.error("Error received: %s", event.error)
            case ListenEvents.SESSION_CREATED, ListenEvents.SESSION_UPDATED:
                logger.info("Session created or updated, session: %s", event.session)
            case _:
                logger.debug(f"Received event: {event}")
        # we put all event in the output buffer, but after the interpreted one.
        await self.receive_buffer.put((event.type, event))

    @override
    async def start_sending(self, **kwargs: Any) -> None:
        while True:
            item = await self.send_buffer.get()
            if not item:
                continue
            if isinstance(item, tuple):
                event, data = item
            else:
                event = item
                data = {}
            if not isinstance(event, SendEvents):
                event = SendEvents(event)
            response: dict[str, Any] = {"type": event.value}
            match event:
                case SendEvents.SESSION_UPDATE:
                    if "settings" not in data:
                        logger.error("Event data does not contain 'settings'")
                    response["session"] = data["settings"].prepare_settings_dict()
                case SendEvents.CONVERSATION_ITEM_CREATE:
                    if "item" not in data:
                        logger.error("Event data does not contain 'item'")
                        return
                    content = data["item"]
                    for item in content.items:
                        match item:
                            case TextContent():
                                response["item"] = ConversationItemParam(
                                    type="message",
                                    content=[
                                        {
                                            "type": "input_text",
                                            "text": item.text,
                                        }
                                    ],
                                    role="user",
                                )

                            case FunctionCallContent():
                                call_id = item.metadata.get("call_id")
                                if not call_id:
                                    logger.error("Function call needs to have a call_id")
                                    continue
                                response["item"] = ConversationItemParam(
                                    type="function_call",
                                    name=item.name,
                                    arguments=item.arguments,
                                    call_id=call_id,
                                )

                            case FunctionResultContent():
                                call_id = item.metadata.get("call_id")
                                if not call_id:
                                    logger.error("Function result needs to have a call_id")
                                    continue
                                response["item"] = ConversationItemParam(
                                    type="function_call_output",
                                    output=item.result,
                                    call_id=call_id,
                                )

                case SendEvents.CONVERSATION_ITEM_TRUNCATE:
                    if "item_id" not in data:
                        logger.error("Event data does not contain 'item_id'")
                        return
                    response["item_id"] = data["item_id"]
                    response["content_index"] = 0
                    response["audio_end_ms"] = data.get("audio_end_ms", 0)

                case SendEvents.CONVERSATION_ITEM_DELETE:
                    if "item_id" not in data:
                        logger.error("Event data does not contain 'item_id'")
                        return
                    response["item_id"] = data["item_id"]
                case SendEvents.RESPONSE_CREATE:
                    if "response" in data:
                        response["response"] = data["response"]
                case SendEvents.RESPONSE_CANCEL:
                    if "response_id" in data:
                        response["response_id"] = data["response_id"]

            if self.data_channel:
                while self.data_channel.readyState != "open":
                    await asyncio.sleep(0.1)
                try:
                    self.data_channel.send(json.dumps(response))
                except Exception as e:
                    logger.error(f"Failed to send event {event} with error: {e!s}")

    @override
    async def create_session(
        self,
        settings: PromptExecutionSettings | None = None,
        chat_history: ChatHistory | None = None,
        audio_track: MediaStreamTrack | None = None,
        **kwargs: Any,
    ) -> None:
        """Create a session in the service."""
        ice_servers = [RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
        self.peer_connection = RTCPeerConnection(configuration=RTCConfiguration(iceServers=ice_servers))

        self.peer_connection.on("track")(self._on_track)

        self.data_channel = self.peer_connection.createDataChannel("oai-events", protocol="json")
        self.data_channel.on("message")(self._on_data)

        self.peer_connection.addTransceiver(audio_track or SKAudioTrack(), "sendrecv")

        offer = await self.peer_connection.createOffer()
        await self.peer_connection.setLocalDescription(offer)

        try:
            ephemeral_token = await self.get_ephemeral_token()
            headers = {"Authorization": f"Bearer {ephemeral_token}", "Content-Type": "application/sdp"}

            async with (
                ClientSession() as session,
                session.post(
                    f"{self.client.beta.realtime._client.base_url}realtime?model={self.ai_model_id}",
                    headers=headers,
                    data=offer.sdp,
                ) as response,
            ):
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"OpenAI WebRTC error: {error_text}")

                sdp_answer = await response.text()
                answer = RTCSessionDescription(sdp=sdp_answer, type="answer")
                await self.peer_connection.setRemoteDescription(answer)
                logger.info("Connected to OpenAI WebRTC")

        except Exception as e:
            logger.error(f"Failed to connect to OpenAI: {e!s}")
            raise

        if settings or chat_history or kwargs:
            await self.update_session(settings=settings, chat_history=chat_history, **kwargs)

    @override
    async def update_session(
        self,
        settings: PromptExecutionSettings | None = None,
        chat_history: ChatHistory | None = None,
        create_response: bool = True,
        **kwargs: Any,
    ) -> None:
        if "kernel" in kwargs:
            self.kernel = kwargs["kernel"]
        if settings:
            self._current_settings = settings
        if self._current_settings and self.kernel:
            self._current_settings = prepare_settings_for_function_calling(
                self._current_settings,
                self.get_prompt_execution_settings_class(),
                self._update_function_choice_settings_callback(),
                kernel=self.kernel,  # type: ignore
            )
            await self.send_buffer.put((SendEvents.SESSION_UPDATE, {"settings": self._current_settings}))
        if chat_history and len(chat_history) > 0:
            for msg in chat_history.messages:
                await self.send_buffer.put((SendEvents.CONVERSATION_ITEM_CREATE, {"item": msg}))
        if create_response:
            await self.send_buffer.put(SendEvents.RESPONSE_CREATE)

    @override
    async def close_session(self) -> None:
        """Close the session in the service."""
        if self.peer_connection:
            with contextlib.suppress(asyncio.CancelledError):
                await self.peer_connection.close()
        self.peer_connection = None
        if self.data_channel:
            with contextlib.suppress(asyncio.CancelledError):
                self.data_channel.close()
        self.data_channel = None

    async def _handle_function_call_arguments_done(
        self,
        event: RealtimeServerEvent,
    ) -> None:
        """Handle response function call done."""
        plugin_name, function_name = self._call_id_to_function_map.pop(event.call_id, "-").split("-", 1)
        if not plugin_name or not function_name:
            logger.error("Function call needs to have a plugin name and function name")
            return
        item = FunctionCallContent(
            id=event.item_id,
            plugin_name=plugin_name,
            function_name=function_name,
            arguments=event.arguments,
            index=event.output_index,
            metadata={"call_id": event.call_id},
        )
        if not self.kernel and not self._current_settings.function_choice_behavior.auto_invoke_kernel_functions:
            return
        chat_history = ChatHistory()
        await self.kernel.invoke_function_call(item, chat_history)
        created_output = chat_history.messages[-1]
        # This returns the output to the service
        await self.send_buffer.put((SendEvents.CONVERSATION_ITEM_CREATE, {"item": created_output}))
        # The model doesn't start responding to the tool call automatically, so triggering it here.
        await self.send_buffer.put(SendEvents.RESPONSE_CREATE)
        # This allows a user to have a full conversation in his code
        await self.receive_buffer.put((ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE, created_output))

    async def get_ephemeral_token(self) -> str:
        """Get an ephemeral token from OpenAI."""
        headers = {"Authorization": f"Bearer {self.client.api_key}", "Content-Type": "application/json"}
        data = {"model": self.ai_model_id, "voice": "echo"}

        try:
            async with (
                ClientSession() as session,
                session.post(
                    f"{self.client.beta.realtime._client.base_url}/realtime/sessions", headers=headers, json=data
                ) as response,
            ):
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    raise Exception(f"Failed to get ephemeral token: {error_text}")

                result = await response.json()
                return result["client_secret"]["value"]

        except Exception as e:
            logger.error(f"Failed to get ephemeral token: {e!s}")
            raise

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (  # noqa
            OpenAIRealtimeExecutionSettings,
        )

        return OpenAIRealtimeExecutionSettings

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_call_configuration
