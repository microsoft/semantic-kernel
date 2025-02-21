# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar, Literal

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai.types.beta.realtime import (
    RealtimeClientEvent,
    RealtimeServerEvent,
    ResponseFunctionCallArgumentsDoneEvent,
)
from pydantic import PrivateAttr

from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import (
    prepare_settings_for_function_calling,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_realtime_execution_settings import (
    OpenAIRealtimeExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.realtime.const import ListenEvents, SendEvents
from semantic_kernel.connectors.ai.open_ai.services.realtime.utils import (
    _create_openai_realtime_client_event,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.realtime_client_base import RealtimeClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.realtime_events import (
    RealtimeAudioEvent,
    RealtimeEvent,
    RealtimeEvents,
    RealtimeFunctionCallEvent,
    RealtimeFunctionResultEvent,
    RealtimeTextEvent,
)
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory


logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class OpenAIRealtimeBase(OpenAIHandler, RealtimeClientBase):
    """OpenAI Realtime service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True
    protocol: ClassVar[Literal["websocket", "webrtc"]] = "websocket"
    kernel: Kernel | None = None

    _current_settings: PromptExecutionSettings | None = PrivateAttr(default=None)
    _call_id_to_function_map: dict[str, str] = PrivateAttr(default_factory=dict)

    async def _parse_event(self, event: RealtimeServerEvent) -> AsyncGenerator[RealtimeEvents, None]:
        """Handle all events but audio delta.

        Audio delta has to be handled by the implementation of the protocol as some
        protocols have different ways of handling audio.

        We put all event in the output buffer, but after the interpreted one.
        so when dealing with them, make sure to check the type of the event, since they
        might be of different types.
        """
        match event.type:
            case ListenEvents.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value:
                yield RealtimeTextEvent(
                    service_type=event.type,
                    service_event=event,
                    text=StreamingTextContent(
                        inner_content=event,
                        text=event.delta,  # type: ignore
                        choice_index=0,
                    ),
                )
            case ListenEvents.RESPONSE_OUTPUT_ITEM_ADDED.value:
                if event.item.type == "function_call" and event.item.call_id and event.item.name:  # type: ignore
                    self._call_id_to_function_map[event.item.call_id] = event.item.name  # type: ignore
                yield RealtimeEvent(service_type=event.type, service_event=event)
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DELTA.value:
                yield RealtimeFunctionCallEvent(
                    service_type=event.type,
                    service_event=event,
                    function_call=FunctionCallContent(
                        id=event.item_id,  # type: ignore
                        name=self._call_id_to_function_map[event.call_id],  # type: ignore
                        arguments=event.delta,  # type: ignore
                        index=event.output_index,  # type: ignore
                        metadata={"call_id": event.call_id},  # type: ignore
                        inner_content=event,
                    ),
                )
            case ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE.value:
                async for parsed_event in self._parse_function_call_arguments_done(event):  # type: ignore
                    if parsed_event:
                        yield parsed_event
            case ListenEvents.ERROR.value:
                logger.error("Error received: %s", event.error.model_dump_json())  # type: ignore
                yield RealtimeEvent(service_type=event.type, service_event=event)
            case ListenEvents.SESSION_CREATED.value | ListenEvents.SESSION_UPDATED.value:
                logger.info("Session created or updated, session: %s", event.session.model_dump_json())  # type: ignore
                yield RealtimeEvent(service_type=event.type, service_event=event)
            case _:
                logger.debug(f"Received event: {event}")
                yield RealtimeEvent(service_type=event.type, service_event=event)

    @override
    async def update_session(
        self,
        chat_history: ChatHistory | None = None,
        settings: PromptExecutionSettings | None = None,
        create_response: bool = False,
        **kwargs: Any,
    ) -> None:
        """Update the session in the service.

        Args:
            chat_history: Chat history.
            settings: Prompt execution settings, if kernel is linked to the service or passed as
                Kwargs, it will be used to update the settings for function calling.
            create_response: Create a response, get the model to start responding, default is False.
            kwargs: Additional arguments, if 'kernel' is passed, it will be used to update the
                settings for function calling, others will be ignored.

        """
        if kwargs:
            if self._create_kwargs:
                kwargs = {**self._create_kwargs, **kwargs}
        else:
            kwargs = self._create_kwargs or {}
        if settings:
            self._current_settings = settings
        if "kernel" in kwargs:
            self.kernel = kwargs["kernel"]

        if self._current_settings:
            if self.kernel:
                self._current_settings = prepare_settings_for_function_calling(
                    self._current_settings,
                    self.get_prompt_execution_settings_class(),
                    self._update_function_choice_settings_callback(),
                    kernel=self.kernel,  # type: ignore
                )
            await self.send(
                RealtimeEvent(
                    service_type=SendEvents.SESSION_UPDATE,
                    service_event={"settings": self._current_settings},
                )
            )

        if chat_history and len(chat_history) > 0:
            for msg in chat_history.messages:
                for item in msg.items:
                    match item:
                        case TextContent():
                            await self.send(
                                RealtimeTextEvent(service_type=SendEvents.CONVERSATION_ITEM_CREATE, text=item)
                            )
                        case FunctionCallContent():
                            await self.send(
                                RealtimeFunctionCallEvent(
                                    service_type=SendEvents.CONVERSATION_ITEM_CREATE, function_call=item
                                )
                            )
                        case FunctionResultContent():
                            await self.send(
                                RealtimeFunctionResultEvent(
                                    service_type=SendEvents.CONVERSATION_ITEM_CREATE, function_result=item
                                )
                            )
                        case _:
                            logger.error("Unsupported item type: %s", item)

        if create_response or kwargs.get("create_response", False) is True:
            await self.send(RealtimeEvent(service_type=SendEvents.RESPONSE_CREATE))

    async def _parse_function_call_arguments_done(
        self,
        event: ResponseFunctionCallArgumentsDoneEvent,
    ) -> AsyncGenerator[RealtimeEvents | None]:
        """Handle response function call done.

        This always yields at least 1 event, either a RealtimeEvent or a RealtimeFunctionResultEvent with the raw event.

        It then also yields any function results both back to the service, through `send` and to the developer.

        """
        # Step 1: check if function calling enabled:
        if not self.kernel or (
            self._current_settings
            and self._current_settings.function_choice_behavior
            and not self._current_settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            yield RealtimeEvent(service_type=event.type, service_event=event)
            return
        # Step 2: check if there is a function that can be found.
        plugin_name, function_name = self._call_id_to_function_map.pop(event.call_id, "-").split("-", 1)
        if not plugin_name or not function_name:
            logger.error("Function call needs to have a plugin name and function name")
            yield RealtimeEvent(service_type=event.type, service_event=event)
            return

        # Step 3: Parse into the function call content, and yield that.
        item = FunctionCallContent(
            id=event.item_id,
            plugin_name=plugin_name,
            function_name=function_name,
            arguments=event.arguments,
            index=event.output_index,
            metadata={"call_id": event.call_id},
        )
        yield RealtimeFunctionCallEvent(
            service_type=ListenEvents.RESPONSE_FUNCTION_CALL_ARGUMENTS_DONE, function_call=item, service_event=event
        )

        # Step 4: Invoke the function call
        chat_history = ChatHistory()
        await self.kernel.invoke_function_call(item, chat_history)
        created_output: FunctionResultContent = chat_history.messages[-1].items[0]  # type: ignore
        # Step 5: Create the function result event
        result = RealtimeFunctionResultEvent(
            service_type=SendEvents.CONVERSATION_ITEM_CREATE,
            function_result=created_output,
        )
        # Step 6: send the result to the service and call `create response`
        await self.send(result)
        await self.send(RealtimeEvent(service_type=SendEvents.RESPONSE_CREATE))
        # Step 7: yield the function result back to the developer as well
        yield result

    async def _send(self, event: RealtimeClientEvent) -> None:
        """Send an event to the service."""
        raise NotImplementedError

    @override
    async def send(self, event: RealtimeEvents, **kwargs: Any) -> None:
        match event:
            case RealtimeAudioEvent():
                await self._send(
                    _create_openai_realtime_client_event(
                        event_type=SendEvents.INPUT_AUDIO_BUFFER_APPEND, audio=event.audio.data_string
                    )
                )
            case RealtimeTextEvent():
                await self._send(
                    _create_openai_realtime_client_event(
                        event_type=SendEvents.CONVERSATION_ITEM_CREATE,
                        **dict(
                            type="message",
                            content=[
                                {
                                    "type": "input_text",
                                    "text": event.text.text,
                                }
                            ],
                            role="user",
                        ),
                    )
                )
            case RealtimeFunctionCallEvent():
                await self._send(
                    _create_openai_realtime_client_event(
                        event_type=SendEvents.CONVERSATION_ITEM_CREATE,
                        **dict(
                            type="function_call",
                            name=event.function_call.name or event.function_call.function_name,
                            arguments=""
                            if not event.function_call.arguments
                            else event.function_call.arguments
                            if isinstance(event.function_call.arguments, str)
                            else json.dumps(event.function_call.arguments),
                            call_id=event.function_call.metadata.get("call_id"),
                        ),
                    )
                )
            case RealtimeFunctionResultEvent():
                await self._send(
                    _create_openai_realtime_client_event(
                        event_type=SendEvents.CONVERSATION_ITEM_CREATE,
                        **dict(
                            type="function_call_output",
                            output=event.function_result.result,
                            call_id=event.function_result.metadata.get("call_id"),
                        ),
                    )
                )
            case _:
                data = event.service_event
                match event.service_type:
                    case SendEvents.SESSION_UPDATE:
                        if not data:
                            logger.error("Event data is empty")
                            return
                        settings = data.get("settings", None)
                        if not settings:
                            logger.error("Event data does not contain 'settings'")
                            return
                        if not isinstance(settings, OpenAIRealtimeExecutionSettings):
                            try:
                                settings = self.get_prompt_execution_settings_from_settings(settings)
                            except Exception as e:
                                logger.error(
                                    f"Failed to properly create settings from passed settings: {settings}, error: {e}"
                                )
                                return
                        assert isinstance(settings, OpenAIRealtimeExecutionSettings)  # nosec
                        if not settings.ai_model_id:
                            settings.ai_model_id = self.ai_model_id
                        await self._send(
                            _create_openai_realtime_client_event(
                                event_type=event.service_type,
                                session=settings.prepare_settings_dict(),
                            )
                        )
                    case SendEvents.INPUT_AUDIO_BUFFER_APPEND:
                        if not data or "audio" not in data:
                            logger.error("Event data does not contain 'audio'")
                            return
                        await self._send(
                            _create_openai_realtime_client_event(
                                event_type=event.service_type,
                                audio=data["audio"],
                            )
                        )
                    case SendEvents.INPUT_AUDIO_BUFFER_COMMIT:
                        await self._send(_create_openai_realtime_client_event(event_type=event.service_type))
                    case SendEvents.INPUT_AUDIO_BUFFER_CLEAR:
                        await self._send(_create_openai_realtime_client_event(event_type=event.service_type))
                    case SendEvents.CONVERSATION_ITEM_CREATE:
                        if not data or "item" not in data:
                            logger.error("Event data does not contain 'item'")
                            return
                        content = data["item"]
                        contents = content.items if isinstance(content, ChatMessageContent) else [content]
                        for item in contents:
                            match item:
                                case TextContent():
                                    await self._send(
                                        _create_openai_realtime_client_event(
                                            event_type=event.service_type,
                                            **dict(
                                                type="message",
                                                content=[
                                                    {
                                                        "type": "input_text",
                                                        "text": item.text,
                                                    }
                                                ],
                                                role="user",
                                            ),
                                        )
                                    )
                                case FunctionCallContent():
                                    await self._send(
                                        _create_openai_realtime_client_event(
                                            event_type=event.service_type,
                                            **dict(
                                                type="function_call",
                                                name=item.name or item.function_name,
                                                arguments=""
                                                if not item.arguments
                                                else item.arguments
                                                if isinstance(item.arguments, str)
                                                else json.dumps(item.arguments),
                                                call_id=item.metadata.get("call_id"),
                                            ),
                                        )
                                    )

                                case FunctionResultContent():
                                    await self._send(
                                        _create_openai_realtime_client_event(
                                            event_type=event.service_type,
                                            **dict(
                                                type="function_call_output",
                                                output=item.result,
                                                call_id=item.metadata.get("call_id"),
                                            ),
                                        )
                                    )
                    case SendEvents.CONVERSATION_ITEM_TRUNCATE:
                        if not data or "item_id" not in data:
                            logger.error("Event data does not contain 'item_id'")
                            return
                        await self._send(
                            _create_openai_realtime_client_event(
                                event_type=event.service_type,
                                item_id=data["item_id"],
                                content_index=0,
                                audio_end_ms=data.get("audio_end_ms", 0),
                            )
                        )
                    case SendEvents.CONVERSATION_ITEM_DELETE:
                        if not data or "item_id" not in data:
                            logger.error("Event data does not contain 'item_id'")
                            return
                        await self._send(
                            _create_openai_realtime_client_event(
                                event_type=event.service_type,
                                item_id=data["item_id"],
                            )
                        )
                    case SendEvents.RESPONSE_CREATE:
                        await self._send(
                            _create_openai_realtime_client_event(
                                event_type=event.service_type, event_id=data.get("event_id", None) if data else None
                            )
                        )
                    case SendEvents.RESPONSE_CANCEL:
                        await self._send(
                            _create_openai_realtime_client_event(
                                event_type=event.service_type,
                                response_id=data.get("response_id", None) if data else None,
                            )
                        )

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
