# Copyright (c) Microsoft. All rights reserved.

import asyncio
import contextlib
import json
import logging
import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, ClassVar, Literal, cast

from pydantic import Field

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from aiohttp import ClientSession
from aiortc import (
    RTCConfiguration,
    RTCDataChannel,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
from av.audio.frame import AudioFrame
from openai._models import construct_type_unchecked
from openai.types.beta.realtime.conversation_item_param import ConversationItemParam
from openai.types.beta.realtime.realtime_server_event import RealtimeServerEvent

from semantic_kernel.connectors.ai.open_ai.services.realtime.const import ListenEvents, SendEvents
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_base import OpenAIRealtimeBase
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeEvent
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.realtime_event import AudioEvent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from aiortc import MediaStreamTrack

    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIRealtimeWebRTCBase(OpenAIRealtimeBase):
    """OpenAI WebRTC Realtime service."""

    protocol: ClassVar[Literal["webrtc"]] = "webrtc"
    peer_connection: RTCPeerConnection | None = None
    data_channel: RTCDataChannel | None = None
    receive_buffer: asyncio.Queue[RealtimeEvent] = Field(default_factory=asyncio.Queue)

    # region public methods

    @override
    async def start_listening(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        create_response: bool = False,
        **kwargs: Any,
    ) -> AsyncGenerator[RealtimeEvent, None]:
        if chat_history or settings or create_response:
            await self.update_session(settings=settings, chat_history=chat_history, create_response=create_response)
        while True:
            event = await self.receive_buffer.get()
            yield event

    @override
    async def start_sending(self, **kwargs: Any) -> None:
        if not self.data_channel:
            logger.error("Data channel not initialized")
            return
        while self.data_channel.readyState != "open":
            await asyncio.sleep(0.1)
        while True:
            event = await self.send_buffer.get()
            response: dict[str, Any] = {"type": event.event_type}
            match event.event_type:
                case SendEvents.SESSION_UPDATE:
                    if "settings" not in event.data:
                        logger.error("Event data does not contain 'settings'")
                    response["session"] = event.data["settings"].prepare_settings_dict()
                case SendEvents.CONVERSATION_ITEM_CREATE:
                    if "item" not in event.data:
                        logger.error("Event data does not contain 'item'")
                        return
                    content = event.data["item"]
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
                                    name=item.name or item.function_name,
                                    arguments=""
                                    if not item.arguments
                                    else item.arguments
                                    if isinstance(item.arguments, str)
                                    else json.dumps(item.arguments),
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
                    if "item_id" not in event.data:
                        logger.error("Event data does not contain 'item_id'")
                        return
                    response["item_id"] = event.data["item_id"]
                    response["content_index"] = 0
                    response["audio_end_ms"] = event.data.get("audio_end_ms", 0)

                case SendEvents.CONVERSATION_ITEM_DELETE:
                    if "item_id" not in event.data:
                        logger.error("Event data does not contain 'item_id'")
                        return
                    response["item_id"] = event.data["item_id"]
                case SendEvents.RESPONSE_CREATE:
                    if "response" in event.data:
                        response["response"] = event.data["response"]
                case SendEvents.RESPONSE_CANCEL:
                    if "response_id" in event.data:
                        response["response_id"] = event.data["response_id"]

            try:
                self.data_channel.send(json.dumps(response))
            except Exception as e:
                logger.error(f"Failed to send event {event} with error: {e!s}")

    @override
    async def create_session(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        audio_track: "MediaStreamTrack | None" = None,
        **kwargs: Any,
    ) -> None:
        """Create a session in the service."""
        if not audio_track:
            from semantic_kernel.connectors.ai.utils.realtime_helpers import SKAudioTrack

            audio_track = SKAudioTrack()

        self.peer_connection = RTCPeerConnection(
            configuration=RTCConfiguration(iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")])
        )

        # track is the audio track being returned from the service
        self.peer_connection.on("track")(self._on_track)

        # data channel is used to send and receive messages
        self.data_channel = self.peer_connection.createDataChannel("oai-events", protocol="json")
        self.data_channel.on("message")(self._on_data)

        # this is the incoming audio, which sends audio to the service
        self.peer_connection.addTransceiver(audio_track)

        offer = await self.peer_connection.createOffer()
        await self.peer_connection.setLocalDescription(offer)

        try:
            ephemeral_token = await self._get_ephemeral_token()
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

    # region implementation specifics

    async def _on_track(self, track: "MediaStreamTrack") -> None:
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
                if self.audio_output_callback:
                    await self.audio_output_callback(frame.to_ndarray())

            except Exception as e:
                logger.error(f"Error playing remote audio frame: {e!s}")
            try:
                await self.receive_buffer.put(
                    AudioEvent(
                        event_type="audio",
                        service_type=ListenEvents.RESPONSE_AUDIO_DELTA,
                        audio=AudioContent(data=frame.to_ndarray(), data_format="np.int16", inner_content=frame),  # type: ignore
                    ),
                )
            except Exception as e:
                logger.error(f"Error processing remote audio frame: {e!s}")
            await asyncio.sleep(0.01)

    async def _on_data(self, data: str) -> None:
        """This method is called whenever a data channel message is received.

        The data is parsed into a RealtimeServerEvent (by OpenAI code) and then processed.
        Audio data is not send through this channel, use _on_track for that.
        """
        try:
            event = cast(
                RealtimeServerEvent,
                construct_type_unchecked(value=json.loads(data), type_=cast(Any, RealtimeServerEvent)),
            )
        except Exception as e:
            logger.error(f"Failed to parse event {data} with error: {e!s}")
            return
        async for parsed_event in self._parse_event(event):
            await self.receive_buffer.put(parsed_event)

    async def _get_ephemeral_token(self) -> str:
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
