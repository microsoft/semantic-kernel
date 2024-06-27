# Copyright (c) Microsoft. All rights reserved.
#
# Model diagnostics to trace model activities with the OTel semantic conventions.
# This code contains experimental features and may change in the future.
# To enable these features, set one of the following senvironment variables to true:
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE

import json
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.utils.tracing.const import (
    COMPLETION_EVENT,
    COMPLETION_EVENT_COMPLETION,
    COMPLETION_TOKEN,
    ERROR_TYPE,
    FINISH_REASON,
    MAX_TOKEN,
    MODEL,
    OPERATION,
    PROMPT_EVENT,
    PROMPT_EVENT_PROMPT,
    PROMPT_TOKEN,
    RESPONSE_ID,
    SYSTEM,
    TEMPERATURE,
    TOP_P,
)

OTEL_ENABLED_ENV_VAR = "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS"
OTEL_SENSITIVE_ENABLED_ENV_VAR = "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE"


_enable_diagnostics = os.getenv(OTEL_ENABLED_ENV_VAR, "false").lower() in ("true", "1", "t")
_enable_sensitive_events = os.getenv(OTEL_SENSITIVE_ENABLED_ENV_VAR, "false").lower() in ("true", "1", "t")

# Creates a tracer from the global tracer provider
tracer = trace.get_tracer(__name__)


def are_model_diagnostics_enabled() -> bool:
    """Check if model diagnostics are enabled.

    Model diagnostics are enabled if either EnableModelDiagnostics or EnableSensitiveEvents is set.
    """
    return _enable_diagnostics or _enable_sensitive_events


def are_sensitive_events_enabled() -> bool:
    """Check if sensitive events are enabled.

    Sensitive events are enabled if EnableSensitiveEvents is set.
    """
    return _enable_sensitive_events


def start_completion_activity(
    model_name: str, model_provider: str, prompt: str, execution_settings: Optional[PromptExecutionSettings]
) -> Optional[Span]:
    """Start a text or chat completion activity for a given model."""
    if not are_model_diagnostics_enabled():
        return None

    operation_name: str = "chat.completions"

    span = tracer.start_span(f"{operation_name} {model_name}")

    # Set attributes on the span
    span.set_attributes(
        {
            OPERATION: operation_name,
            SYSTEM: model_provider,
            MODEL: model_name,
        }
    )

    if execution_settings is not None:
        attribute = execution_settings.extension_data.get("max_tokens")
        if attribute is not None:
            span.set_attribute(MAX_TOKEN, attribute)

        attribute = execution_settings.extension_data.get("temperature")
        if attribute is not None:
            span.set_attribute(TEMPERATURE, attribute)

        attribute = execution_settings.extension_data.get("top_p")
        if attribute is not None:
            span.set_attribute(TOP_P, attribute)

    if are_sensitive_events_enabled():
        span.add_event(PROMPT_EVENT, {PROMPT_EVENT_PROMPT: prompt})

    return span


def set_completion_response(
    span: Span,
    completions: list[ChatMessageContent],
    finish_reasons: list[str],
    response_id: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
) -> None:
    """Set the a text or chat completion response for a given activity."""
    if not are_model_diagnostics_enabled():
        return

    if prompt_tokens:
        span.set_attribute(PROMPT_TOKEN, prompt_tokens)

    if completion_tokens:
        span.set_attribute(COMPLETION_TOKEN, completion_tokens)

    if finish_reasons:
        span.set_attribute(FINISH_REASON, ",".join(finish_reasons))

    span.set_attribute(RESPONSE_ID, response_id)

    if are_sensitive_events_enabled() and completions:
        span.add_event(COMPLETION_EVENT, {COMPLETION_EVENT_COMPLETION: _messages_to_openai_format(completions)})


def set_completion_error(span: Span, error: Exception) -> None:
    """Set an error for a text or chat completion ."""
    if not are_model_diagnostics_enabled():
        return

    span.set_attribute(ERROR_TYPE, str(type(error)))

    span.set_status(StatusCode.ERROR, str(error))


def _messages_to_openai_format(chat_history: list[ChatMessageContent]) -> str:
    formatted_messages = []
    for message in chat_history:
        message_dict = {"role": message.role, "content": json.dumps(message.content)}
        if any(isinstance(item, FunctionCallContent) for item in message.items):
            message_dict["tool_calls"] = _tool_calls_to_openai_format(message.items)
        formatted_messages.append(json.dumps(message_dict))

    return "[{}]".format(", \n".join(formatted_messages))


def _tool_calls_to_openai_format(items: list[ITEM_TYPES]) -> str:
    tool_calls: list[str] = []
    for item in items:
        if isinstance(item, FunctionCallContent):
            tool_call = {
                "id": item.id,
                "function": {"arguments": json.dumps(item.arguments), "name": item.function_name},
                "type": "function",
            }
            tool_calls.append(json.dumps(tool_call))
    return f"[{', '.join(tool_calls)}]"
