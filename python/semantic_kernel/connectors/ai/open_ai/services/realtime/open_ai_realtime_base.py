# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, ClassVar, Literal

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from numpy import ndarray
from openai.types.beta.realtime.realtime_server_event import RealtimeServerEvent
from openai.types.beta.realtime.response_function_call_arguments_done_event import (
    ResponseFunctionCallArgumentsDoneEvent,
)
from pydantic import PrivateAttr

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import (
    prepare_settings_for_function_calling,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.realtime.const import ListenEvents, SendEvents
from semantic_kernel.connectors.ai.open_ai.services.realtime.utils import (
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIRealtimeBase(OpenAIHandler, RealtimeClientBase):
    """OpenAI Realtime service."""

    protocol: ClassVar[Literal["websocket", "webrtc"]] = "websocket"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True
    audio_output_callback: Callable[[ndarray], Coroutine[Any, Any, None]] | None = None
    kernel: Kernel | None = None

    _current_settings: PromptExecutionSettings | None = PrivateAttr(None)
    _call_id_to_function_map: dict[str, str] = PrivateAttr(default_factory=dict)

    async def _handle_event(self, event: RealtimeServerEvent) -> None:
        """Handle all events but audio delta.

        Audio delta has to be handled by the implementation of the protocol as some
        protocols have different ways of handling audio.
        """
        match event.type:
            case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value:
                await self.receive_buffer.put((
                    event.type,
                    StreamingChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content=event.delta,
                        choice_index=event.content_index,
                        inner_content=event,
                    ),
                ))
            case ListenEvents.RESPONSE_OUTPUT_ITEM_ADDED.value:
                if event.item.type == "function_call" and event.item.call_id and event.item.name:
                    self._call_id_to_function_map[event.item.call_id] = event.item.name
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA.value:
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
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE.value:
                await self._handle_function_call_arguments_done(event)
            case ListenEvents.ERROR.value:
                logger.error("Error received: %s", event.error)
            case ListenEvents.SESSION_CREATED.value, ListenEvents.SESSION_UPDATED.value:
                logger.info("Session created or updated, session: %s", event.session)
            case _:
                logger.debug(f"Received event: {event}")
        # we put all event in the output buffer, but after the interpreted one.
        # so when dealing with them, make sure to check the type of the event, since they
        # might be of different types.
        await self.receive_buffer.put((event.type, event))

    @override
    async def update_session(
        self,
        settings: PromptExecutionSettings | None = None,
        chat_history: ChatHistory | None = None,
        create_response: bool = False,
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
            await self.send(SendEvents.SESSION_UPDATE, settings=self._current_settings)
        if chat_history and len(chat_history) > 0:
            for msg in chat_history.messages:
                await self.send(SendEvents.CONVERSATION_ITEM_CREATE, item=msg)
        if create_response:
            await self.send(SendEvents.RESPONSE_CREATE)

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

    async def _handle_function_call_arguments_done(
        self,
        event: ResponseFunctionCallArgumentsDoneEvent,
    ) -> None:
        """Handle response function call done."""
        if not self.kernel or (
            self._current_settings
            and self._current_settings.function_choice_behavior
            and not self._current_settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return
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
        chat_history = ChatHistory()
        await self.kernel.invoke_function_call(item, chat_history)
        created_output = chat_history.messages[-1]
        # This returns the output to the service
        await self.send(SendEvents.CONVERSATION_ITEM_CREATE, item=created_output)
        # The model doesn't start responding to the tool call automatically, so triggering it here.
        await self.send(SendEvents.RESPONSE_CREATE)
        # This allows a user to have a full conversation in his code
        await self.receive_buffer.put((ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE, created_output))

    @override
    async def start_listening(
        self, settings: PromptExecutionSettings | None = None, chat_history: ChatHistory | None = None, **kwargs: Any
    ) -> None:
        pass

    @override
    async def start_sending(self, **kwargs: Any) -> None:
        pass

    @override
    async def create_session(
        self, settings: PromptExecutionSettings | None = None, chat_history: ChatHistory | None = None, **kwargs: Any
    ) -> None:
        pass

    @override
    async def close_session(self) -> None:
        pass
