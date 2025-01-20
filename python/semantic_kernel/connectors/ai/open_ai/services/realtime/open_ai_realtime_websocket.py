# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import json
import logging
import sys
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from semantic_kernel.connectors.ai.open_ai.services.realtime.open_ai_realtime_base import OpenAIRealtimeBase

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from openai.types.beta.realtime.conversation_item_param import ConversationItemParam
from pydantic import Field

from semantic_kernel.connectors.ai.open_ai.services.realtime.const import ListenEvents, SendEvents
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory

logger: logging.Logger = logging.getLogger(__name__)

# region Websocket


@experimental_class
class OpenAIRealtimeWebsocketBase(OpenAIRealtimeBase):
    """OpenAI Realtime service."""

    protocol: ClassVar[Literal["websocket"]] = "websocket"
    connection: AsyncRealtimeConnection | None = None
    connected: asyncio.Event = Field(default_factory=asyncio.Event)

    @override
    async def start_listening(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
        create_response: bool = False,
        **kwargs: Any,
    ) -> None:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection is not established.")

        if chat_history or settings or create_response:
            await self.update_session(settings=settings, chat_history=chat_history, create_response=create_response)

        async for event in self.connection:
            if event.type == ListenEvents.RESPONSE_AUDIO_DELTA.value:
                if self.audio_output:
                    out = self.audio_output(event)
                    if isawaitable(out):
                        await out
                try:
                    await self.receive_buffer.put((
                        event.type,
                        StreamingChatMessageContent(
                            role=AuthorRole.ASSISTANT,
                            items=[
                                AudioContent(
                                    data=base64.b64decode(event.delta),
                                    data_format="base64",
                                    inner_content=event,
                                )
                            ],  # type: ignore
                            choice_index=event.content_index,
                        ),
                    ))
                except Exception as e:
                    logger.error(f"Error processing remote audio frame: {e!s}")
            else:
                await self._handle_event(event)

    @override
    async def start_sending(self, **kwargs: Any) -> None:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection is not established.")
        while True:
            event, data = await self.send_buffer.get()
            match event:
                case SendEvents.SESSION_UPDATE:
                    if "settings" not in data:
                        logger.error("Event data does not contain 'settings'")
                    await self.connection.session.update(session=data["settings"].prepare_settings_dict())
                case SendEvents.INPUT_AUDIO_BUFFER_APPEND:
                    if "content" not in data:
                        logger.error("Event data does not contain 'content'")
                        return
                    await self.connection.input_audio_buffer.append(audio=data["content"].data.decode("utf-8"))
                case SendEvents.INPUT_AUDIO_BUFFER_COMMIT:
                    await self.connection.input_audio_buffer.commit()
                case SendEvents.INPUT_AUDIO_BUFFER_CLEAR:
                    await self.connection.input_audio_buffer.clear()
                case SendEvents.CONVERSATION_ITEM_CREATE:
                    if "item" not in data:
                        logger.error("Event data does not contain 'item'")
                        return
                    content = data["item"]
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
                                        name=item.name or item.function_name,
                                        arguments=""
                                        if not item.arguments
                                        else item.arguments
                                        if isinstance(item.arguments, str)
                                        else json.dumps(item.arguments),
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
                    if "item_id" not in data:
                        logger.error("Event data does not contain 'item_id'")
                        return
                    await self.connection.conversation.item.truncate(
                        item_id=data["item_id"], content_index=0, audio_end_ms=data.get("audio_end_ms", 0)
                    )
                case SendEvents.CONVERSATION_ITEM_DELETE:
                    if "item_id" not in data:
                        logger.error("Event data does not contain 'item_id'")
                        return
                    await self.connection.conversation.item.delete(item_id=data["item_id"])
                case SendEvents.RESPONSE_CREATE:
                    if "response" in data:
                        await self.connection.response.create(response=data["response"])
                    else:
                        await self.connection.response.create()
                case SendEvents.RESPONSE_CANCEL:
                    if "response_id" in data:
                        await self.connection.response.cancel(response_id=data["response_id"])
                    else:
                        await self.connection.response.cancel()

    @override
    async def create_session(
        self,
        settings: "PromptExecutionSettings | None" = None,
        chat_history: "ChatHistory | None" = None,
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
