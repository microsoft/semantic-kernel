# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import logging
import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, ClassVar, Literal

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import numpy as np
from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from openai.types.beta.realtime.realtime_client_event import RealtimeClientEvent
from pydantic import Field

from semantic_kernel.connectors.ai.open_ai.services.realtime.const import ListenEvents
from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_base import OpenAIRealtimeBase
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.realtime_events.realtime_event import RealtimeAudioEvent, RealtimeEvents
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIRealtimeWebsocketBase(OpenAIRealtimeBase):
    """OpenAI Realtime service."""

    protocol: ClassVar[Literal["websocket"]] = "websocket"  # type: ignore
    connection: AsyncRealtimeConnection | None = None
    connected: asyncio.Event = Field(default_factory=asyncio.Event)

    @override
    async def receive(
        self,
        **kwargs: Any,
    ) -> AsyncGenerator[RealtimeEvents, None]:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection is not established.")

        async for event in self.connection:
            if event.type == ListenEvents.RESPONSE_AUDIO_DELTA.value:
                if self.audio_output_callback:
                    await self.audio_output_callback(np.frombuffer(base64.b64decode(event.delta), dtype=np.int16))
                yield RealtimeAudioEvent(
                    audio=AudioContent(data=event.delta, data_format="base64", inner_content=event),
                    service_type=event.type,
                    service_event=event,
                )
                continue
            async for realtime_event in self._parse_event(event):
                yield realtime_event

    async def _send(self, event: RealtimeClientEvent) -> None:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection is not established.")
        try:
            await self.connection.send(event)
        except Exception as e:
            logger.error(f"Error sending response: {e!s}")

    @override
    async def create_session(
        self,
        chat_history: "ChatHistory | None" = None,
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> None:
        """Create a session in the service."""
        self.connection = await self.client.beta.realtime.connect(model=self.ai_model_id).enter()
        self.connected.set()
        if settings or chat_history or kwargs:
            await self.update_session(settings=settings, chat_history=chat_history, **kwargs)

    @override
    async def close_session(self) -> None:
        """Close the session in the service."""
        if self.connected.is_set() and self.connection:
            await self.connection.close()
            self.connection = None
            self.connected.clear()
