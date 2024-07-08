# Copyright (c) Microsoft. All rights reserved.
#
# Code to trace model activities with the OTel semantic conventions.
# This code contains experimental features and may change in the future.
# To enable these features, set one of the following senvironment variables to true:
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE

import functools
import json
import os
from collections.abc import Callable
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
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


def trace_chat_completion(model_provider: str) -> Callable:
    """Decorator to trace chat completion activities."""

    def inner_trace_chat_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(*args: Any, **kwargs: Any) -> list[ChatMessageContent]:
            chat_history: ChatHistory = kwargs["chat_history"]
            settings: PromptExecutionSettings = kwargs["settings"]

            if hasattr(settings, "ai_model_id") and settings.ai_model_id:
                model_name = settings.ai_model_id
            elif hasattr(args[0], "ai_model_id") and args[0].ai_model_id:
                model_name = args[0].ai_model_id
            else:
                model_name = "unknown"

            span = _start_completion_activity(model_name, model_provider, chat_history, settings)

            try:
                completions: list[ChatMessageContent] = await completion_func(*args, **kwargs)
            except Exception as exception:
                if span:
                    _set_completion_error(span, exception)
                    span.end()
                raise

            if span:
                with trace.use_span(span, end_on_exit=True):
                    if completions:
                        first_completion = completions[0]
                        response_id = first_completion.metadata.get("id", None)
                        if not response_id:
                            response_id = (
                                first_completion.inner_content.get("id", None)
                                if first_completion.inner_content
                                else None
                            )
                        usage = first_completion.metadata.get("usage", None)
                        prompt_tokens = usage.prompt_tokens if hasattr(usage, "prompt_tokens") else None
                        completion_tokens = usage.completion_tokens if hasattr(usage, "completion_tokens") else None
                    _set_completion_response(
                        span, completions, response_id or "unknown", prompt_tokens, completion_tokens
                    )

            return completions

        return wrapper_decorator

    return inner_trace_chat_completion


def _start_completion_activity(
    model_name: str, model_provider: str, chat_history: ChatHistory, execution_settings: PromptExecutionSettings | None
) -> Span | None:
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

    if execution_settings:
        attribute = execution_settings.extension_data.get("max_tokens")
        if attribute:
            span.set_attribute(MAX_TOKEN, attribute)

        attribute = execution_settings.extension_data.get("temperature")
        if attribute:
            span.set_attribute(TEMPERATURE, attribute)

        attribute = execution_settings.extension_data.get("top_p")
        if attribute:
            span.set_attribute(TOP_P, attribute)

    if are_sensitive_events_enabled():
        formatted_messages = _messages_to_openai_format(chat_history.messages)
        span.add_event(PROMPT_EVENT, {PROMPT_EVENT_PROMPT: formatted_messages})

    return span


def _set_completion_response(
    span: Span,
    completions: list[ChatMessageContent],
    response_id: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> None:
    """Set the a text or chat completion response for a given activity."""
    if not are_model_diagnostics_enabled():
        return

    span.set_attribute(RESPONSE_ID, response_id)

    finish_reasons: list[str] = [str(content.finish_reason) for content in completions]
    span.set_attribute(FINISH_REASON, ",".join(finish_reasons))

    if are_sensitive_events_enabled() and completions:
        span.add_event(COMPLETION_EVENT, {COMPLETION_EVENT_COMPLETION: _messages_to_openai_format(completions)})

    if prompt_tokens:
        span.set_attribute(PROMPT_TOKEN, prompt_tokens)

    if completion_tokens:
        span.set_attribute(COMPLETION_TOKEN, completion_tokens)


def _set_completion_error(span: Span, error: Exception) -> None:
    """Set an error for a text or chat completion ."""
    if not are_model_diagnostics_enabled():
        return

    span.set_attribute(ERROR_TYPE, str(type(error)))

    span.set_status(StatusCode.ERROR, str(error))


def _messages_to_openai_format(messages: list[ChatMessageContent]) -> str:
    """Convert a list of ChatMessageContent to a string in the OpenAI format.

    OpenTelemetry recommends formatting the messages in the OpenAI format
    regardless of the actual model being used.
    """
    formatted_messages = [
        json.dumps(
            {
                "role": message.role,
                "content": json.dumps(message.content),
                **(
                    {"tool_calls": _tool_calls_to_openai_format(message.items)}
                    if any(isinstance(item, FunctionCallContent) for item in message.items)
                    else {}
                ),
            }
        )
        for message in messages
    ]

    return "[{}]".format(", \n".join(formatted_messages))


def _tool_calls_to_openai_format(items: list[ITEM_TYPES]) -> str:
    """Convert a list of FunctionCallContent to a string in the OpenAI format.

    OpenTelemetry recommends formatting the messages in the OpenAI format
    regardless of the actual model being used.
    """
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
