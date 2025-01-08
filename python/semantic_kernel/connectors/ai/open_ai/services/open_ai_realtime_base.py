# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai.resources.beta.realtime.realtime import AsyncRealtimeConnection
from openai.types.beta.realtime.conversation_item_create_event_param import ConversationItemParam
from openai.types.beta.realtime.realtime_server_event import RealtimeServerEvent
from openai.types.beta.realtime.session import Session
from pydantic import Field

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.open_ai_realtime_utils import (
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIRealtimeBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Realtime service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True
    connection: AsyncRealtimeConnection | None = None
    connected: asyncio.Event = Field(default_factory=asyncio.Event)
    session: Session | None = None

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (  # noqa
            OpenAIRealtimeExecutionSettings,
        )

        return OpenAIRealtimeExecutionSettings

    async def _get_connection(self) -> AsyncRealtimeConnection:
        await self.connected.wait()
        if not self.connection:
            raise ValueError("Connection not established")
        return self.connection

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        if not isinstance(settings, self.get_prompt_execution_settings_class()):
            settings = self.get_prompt_execution_settings_from_settings(settings)

        events: list[RealtimeServerEvent] = []
        detailed_events: dict[str, list[RealtimeServerEvent]] = {}
        function_calls: list[StreamingChatMessageContent] = []

        async with self.client.beta.realtime.connect(model=self.ai_model_id) as conn:
            self.connection = conn
            self.connected.set()

            await conn.session.update(session=settings.prepare_settings_dict())
            if len(chat_history) > 0:
                await asyncio.gather(*(self._add_content_to_conversation(msg) for msg in chat_history.messages))

            async for event in conn:
                events.append(event)
                detailed_events.setdefault(event.type, []).append(event)
                match event.type:
                    case "session.created" | "session.updated":
                        self.session = event.session
                        continue
                    case "error":
                        logger.error("Error received: %s", event.error)
                        continue
                    case "response.audio.delta":
                        yield [
                            StreamingChatMessageContent(
                                role=AuthorRole.ASSISTANT,
                                items=[AudioContent(data=base64.b64decode(event.delta), data_format="base64")],
                                choice_index=event.content_index,
                                inner_content=event,
                            )
                        ]
                        continue
                    case "response.audio_transcript.delta":
                        yield [
                            StreamingChatMessageContent(
                                role=AuthorRole.ASSISTANT,
                                items=[StreamingTextContent(text=event.delta, choice_index=event.content_index)],
                                choice_index=event.content_index,
                                inner_content=event,
                            )
                        ]
                        continue
                    case "response.audio_transcript.done":
                        chat_history.add_message(
                            StreamingChatMessageContent(
                                role=AuthorRole.ASSISTANT,
                                items=[StreamingTextContent(text=event.transcript, choice_index=event.content_index)],
                                choice_index=event.content_index,
                                inner_content=event,
                            )
                        )
                    case "response.function_call_arguments.delta":
                        msg = StreamingChatMessageContent(
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
                        )
                        function_calls.append(msg)
                        yield [msg]
                        continue
                    case "response.function_call_arguments.done":
                        # execute function, add result to conversation
                        if len(function_calls) > 0:
                            function_call = sum(function_calls[1:], function_calls[0])
                            # execute function
                            results = []
                            for item in function_call.items:
                                if isinstance(item, FunctionCallContent):
                                    kernel: Kernel | None = kwargs.get("kernel")
                                    call_id = item.name
                                    function_name = next(
                                        output_item_event.item.name
                                        for output_item_event in detailed_events["response.output_item.added"]
                                        if output_item_event.item.call_id == call_id
                                    )
                                    item.plugin_name, item.function_name = function_name.split("-", 1)
                                    if kernel:
                                        await kernel.invoke_function_call(item, chat_history)
                                        # add result to conversation
                                        results.append(chat_history.messages[-1])
                            for message in results:
                                await self._add_content_to_conversation(content=message)
                    case _:
                        logger.debug("Unhandled event type: %s", event.type)
        logger.debug(f"Finished streaming chat message contents, {len(events)} events received.")
        for event_type in detailed_events:
            logger.debug(f"Event type: {event_type}, count: {len(detailed_events[event_type])}")

    async def send_content(
        self,
        content: ChatMessageContent | AudioContent | AsyncGenerator[AudioContent, Any],
        **kwargs: Any,
    ) -> None:
        """Send a chat message content to the service.

        This content should contain audio content, either as a ChatMessageContent with a
        AudioContent item, as AudioContent directly, as or as a generator of AudioContent.

        """
        if isinstance(content, AudioContent | ChatMessageContent):
            if isinstance(content, ChatMessageContent):
                content = next(item for item in content.items if isinstance(item, AudioContent))
            connection = await self._get_connection()
            await connection.input_audio_buffer.append(audio=content.data.decode("utf-8"))
            await asyncio.sleep(0)
            return

        async for audio_content in content:
            if isinstance(audio_content, ChatMessageContent):
                audio_content = next(item for item in audio_content.items if isinstance(item, AudioContent))
            connection = await self._get_connection()
            await connection.input_audio_buffer.append(audio=audio_content.data.decode("utf-8"))
            await asyncio.sleep(0)

    async def commit_content(self, settings: "PromptExecutionSettings") -> None:
        """Commit the chat message content to the service.

        This is only needed when turn detection is not handled by the service.

        This behavior is determined by the turn_detection parameter in the settings.
        If turn_detection is None, then it will commit the audio buffer and
        ask the service to process the audio and create the response.
        """
        if not isinstance(settings, self.get_prompt_execution_settings_class()):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        if not settings.turn_detection:
            connection = await self._get_connection()
            await connection.input_audio_buffer.commit()
            await connection.response.create()

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_call_configuration

    async def _streaming_function_call_result_callback(
        self, function_result_messages: list[StreamingChatMessageContent]
    ) -> None:
        """Callback to handle the streaming function call result messages.

        Override this method to handle the streaming function call result messages.

        Args:
            function_result_messages (list): The streaming function call result messages.
        """
        for msg in function_result_messages:
            await self._add_content_to_conversation(msg)

    async def _add_content_to_conversation(self, content: ChatMessageContent) -> None:
        """Add an item to the conversation."""
        connection = await self._get_connection()
        for item in content.items:
            match item:
                case AudioContent():
                    await connection.conversation.item.create(
                        item=ConversationItemParam(
                            type="message",
                            content=[
                                {
                                    "type": "input_audio",
                                    "audio": item.data.decode("utf-8"),
                                }
                            ],
                            role="user",
                        )
                    )
                case TextContent():
                    await connection.conversation.item.create(
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
                    await connection.conversation.item.create(
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
                    await connection.conversation.item.create(
                        item=ConversationItemParam(
                            type="function_call_output",
                            output=item.result,
                            call_id=call_id,
                        )
                    )
                case _:
                    logger.debug("Unhandled item type: %s", item.__class__.__name__)
                    continue
