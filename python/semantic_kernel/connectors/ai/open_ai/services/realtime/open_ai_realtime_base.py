# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.realtime_event import (
    FunctionCallEvent,
    FunctionResultEvent,
    RealtimeEvent,
    ServiceEvent,
    TextEvent,
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent

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

    async def _parse_event(self, event: RealtimeServerEvent) -> AsyncGenerator[RealtimeEvent, None]:
        """Handle all events but audio delta.

        Audio delta has to be handled by the implementation of the protocol as some
        protocols have different ways of handling audio.
        """
        match event.type:
            case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value:
                yield TextEvent(
                    event_type="text",
                    service_type=event.type,
                    text=StreamingTextContent(
                        inner_content=event,
                        text=event.delta,
                        choice_index=0,
                    ),
                )
            case ListenEvents.RESPONSE_OUTPUT_ITEM_ADDED.value:
                if event.item.type == "function_call" and event.item.call_id and event.item.name:
                    self._call_id_to_function_map[event.item.call_id] = event.item.name
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA.value:
                yield FunctionCallEvent(
                    event_type="function_call",
                    service_type=event.type,
                    function_call=FunctionCallContent(
                        id=event.item_id,
                        name=self._call_id_to_function_map[event.call_id],
                        arguments=event.delta,
                        index=event.output_index,
                        metadata={"call_id": event.call_id},
                        inner_content=event,
                    ),
                )
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE.value:
                async for parsed_event in self._parse_function_call_arguments_done(event):
                    if parsed_event:
                        yield parsed_event
            case ListenEvents.ERROR.value:
                logger.error("Error received: %s", event.error)
            case ListenEvents.SESSION_CREATED.value, ListenEvents.SESSION_UPDATED.value:
                logger.info("Session created or updated, session: %s", event.session)
            case _:
                logger.debug(f"Received event: {event}")
        # we put all event in the output buffer, but after the interpreted one.
        # so when dealing with them, make sure to check the type of the event, since they
        # might be of different types.
        yield ServiceEvent(event_type="service", service_type=event.type, event=event)

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
            await self.send(
                ServiceEvent(event_type="service", service_type=SendEvents.SESSION_UPDATE, event=self._current_settings)
            )
        if chat_history and len(chat_history) > 0:
            for msg in chat_history.messages:
                await self.send(
                    ServiceEvent(event_type="service", service_type=SendEvents.CONVERSATION_ITEM_CREATE, event=msg)
                )
        if create_response:
            await self.send(ServiceEvent(event_type="service", service_type=SendEvents.RESPONSE_CREATE))

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

    async def _parse_function_call_arguments_done(
        self,
        event: ResponseFunctionCallArgumentsDoneEvent,
    ) -> AsyncGenerator[RealtimeEvent | None]:
        """Handle response function call done."""
        if not self.kernel or (
            self._current_settings
            and self._current_settings.function_choice_behavior
            and not self._current_settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            yield None
            return
        plugin_name, function_name = self._call_id_to_function_map.pop(event.call_id, "-").split("-", 1)
        if not plugin_name or not function_name:
            logger.error("Function call needs to have a plugin name and function name")
            yield None
            return
        item = FunctionCallContent(
            id=event.item_id,
            plugin_name=plugin_name,
            function_name=function_name,
            arguments=event.arguments,
            index=event.output_index,
            metadata={"call_id": event.call_id},
        )
        yield FunctionCallEvent(
            event_type="function_call",
            service_type=ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE,
            function_call=item,
        )
        chat_history = ChatHistory()
        await self.kernel.invoke_function_call(item, chat_history)
        created_output: FunctionResultContent = chat_history.messages[-1].items[0]  # type: ignore
        # This returns the output to the service
        await self.send(
            ServiceEvent(event_type="service", service_type=SendEvents.CONVERSATION_ITEM_CREATE, event=created_output)
        )
        # The model doesn't start responding to the tool call automatically, so triggering it here.
        await self.send(ServiceEvent(event_type="service", service_type=SendEvents.RESPONSE_CREATE))
        # This allows a user to have a full conversation in his code
        yield FunctionResultEvent(event_type="function_result", function_result=created_output)

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
