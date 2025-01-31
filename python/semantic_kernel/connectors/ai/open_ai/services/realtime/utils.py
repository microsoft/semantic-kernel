# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from openai.types.beta.realtime import (
    ConversationItem,
    ConversationItemCreateEvent,
    ConversationItemDeleteEvent,
    ConversationItemTruncateEvent,
    InputAudioBufferAppendEvent,
    InputAudioBufferClearEvent,
    InputAudioBufferCommitEvent,
    RealtimeClientEvent,
    ResponseCancelEvent,
    ResponseCreateEvent,
    SessionUpdateEvent,
)
from openai.types.beta.realtime.response_create_event import Response
from openai.types.beta.realtime.session_update_event import Session

from semantic_kernel.connectors.ai.open_ai.services.realtime.const import SendEvents

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_choice_behavior import (
        FunctionCallChoiceConfiguration,
        FunctionChoiceType,
    )
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


def update_settings_from_function_call_configuration(
    function_choice_configuration: "FunctionCallChoiceConfiguration",
    settings: "PromptExecutionSettings",
    type: "FunctionChoiceType",
) -> None:
    """Update the settings from a FunctionChoiceConfiguration."""
    if (
        function_choice_configuration.available_functions
        and hasattr(settings, "tool_choice")
        and hasattr(settings, "tools")
    ):
        settings.tool_choice = type
        settings.tools = [
            kernel_function_metadata_to_function_call_format(f)
            for f in function_choice_configuration.available_functions
        ]


def kernel_function_metadata_to_function_call_format(
    metadata: "KernelFunctionMetadata",
) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "type": "function",
        "name": metadata.fully_qualified_name,
        "description": metadata.description or "",
        "parameters": {
            "type": "object",
            "properties": {
                param.name: param.schema_data for param in metadata.parameters if param.include_in_function_choices
            },
            "required": [p.name for p in metadata.parameters if p.is_required and p.include_in_function_choices],
        },
    }


def _create_openai_realtime_client_event(event_type: SendEvents, **kwargs: Any) -> RealtimeClientEvent:
    match event_type:
        case SendEvents.SESSION_UPDATE:
            return SessionUpdateEvent(
                type=event_type,
                session=Session.model_validate(kwargs.pop("session")),
                **kwargs,
            )
        case SendEvents.INPUT_AUDIO_BUFFER_APPEND:
            return InputAudioBufferAppendEvent(
                type=event_type,
                **kwargs,
            )
        case SendEvents.INPUT_AUDIO_BUFFER_COMMIT:
            return InputAudioBufferCommitEvent(
                type=event_type,
                **kwargs,
            )
        case SendEvents.INPUT_AUDIO_BUFFER_CLEAR:
            return InputAudioBufferClearEvent(
                type=event_type,
                **kwargs,
            )
        case SendEvents.CONVERSATION_ITEM_CREATE:
            if "event_id" in kwargs:
                event_id = kwargs.pop("event_id")
            if "previous_item_id" in kwargs:
                previous_item_id = kwargs.pop("previous_item_id")
            event_kwargs = {"event_id": event_id} if "event_id" in kwargs else {}
            event_kwargs.update({"previous_item_id": previous_item_id} if "previous_item_id" in kwargs else {})
            return ConversationItemCreateEvent(
                type=event_type,
                item=ConversationItem.model_validate(kwargs),
                **event_kwargs,
            )
        case SendEvents.CONVERSATION_ITEM_TRUNCATE:
            return ConversationItemTruncateEvent(
                type=event_type,
                **kwargs,
            )
        case SendEvents.CONVERSATION_ITEM_DELETE:
            return ConversationItemDeleteEvent(
                type=event_type,
                **kwargs,
            )
        case SendEvents.RESPONSE_CREATE:
            event_kwargs = {"event_id": kwargs.pop("event_id")} if "event_id" in kwargs else {}
            return ResponseCreateEvent(
                type=event_type,
                response=Response.model_validate(kwargs),
                **event_kwargs,
            )
        case SendEvents.RESPONSE_CANCEL:
            return ResponseCancelEvent(
                type=event_type,
                **kwargs,
            )
        case _:
            raise ValueError(f"Unknown event type: {event_type}")
