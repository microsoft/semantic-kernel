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

from opentelemetry.trace import Span, StatusCode, get_tracer, use_span

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.telemetry.const import (
    CHAT_COMPLETION_OPERATION,
    COMPLETION_EVENT,
    COMPLETION_EVENT_COMPLETION,
    COMPLETION_TOKENS,
    ERROR_TYPE,
    FINISH_REASON,
    MAX_TOKENS,
    MODEL,
    OPERATION,
    PROMPT_EVENT,
    PROMPT_EVENT_PROMPT,
    PROMPT_TOKENS,
    RESPONSE_ID,
    SYSTEM,
    TEMPERATURE,
    TEXT_COMPLETION_OPERATION,
    TOP_P,
)

OTEL_ENABLED_ENV_VAR = "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS"
OTEL_SENSITIVE_ENABLED_ENV_VAR = (
    "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE"
)


_enable_diagnostics = os.getenv(OTEL_ENABLED_ENV_VAR, "false").lower() in (
    "true",
    "1",
    "t",
)
_enable_sensitive_events = os.getenv(
    OTEL_SENSITIVE_ENABLED_ENV_VAR, "false"
).lower() in ("true", "1", "t")

# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)


def are_model_diagnostics_enabled() -> bool:
    """Check if model diagnostics are enabled.

    Model diagnostics are enabled if either _enable_diagnostics or _enable_sensitive_events is set.
    """
    return _enable_diagnostics or _enable_sensitive_events


def are_sensitive_events_enabled() -> bool:
    """Check if sensitive events are enabled.

    Sensitive events are enabled if _enable_sensitive_events is set.
    """
    return _enable_sensitive_events


def trace_chat_completion(model_provider: str) -> Callable:
    """Decorator to trace chat completion activities."""

    def inner_trace_chat_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(
            *args: Any, **kwargs: Any
        ) -> list[ChatMessageContent]:
            chat_history: ChatHistory = kwargs["chat_history"]
            settings: PromptExecutionSettings = kwargs["settings"]

            model_name = (
                getattr(settings, "ai_model_id", None)
                or getattr(args[0], "ai_model_id", None)
                or "unknown"
            )

            formatted_messages = (
                _messages_to_openai_format(chat_history.messages)
                if are_sensitive_events_enabled()
                else None
            )
            span = _start_completion_activity(
                CHAT_COMPLETION_OPERATION,
                model_name,
                model_provider,
                formatted_messages,
                settings,
            )

            try:
                completions: list[ChatMessageContent] = await completion_func(
                    *args, **kwargs
                )
            except Exception as exception:
                if span:
                    _set_completion_error(span, exception)
                    span.end()
                raise

            if span and completions:
                with use_span(span, end_on_exit=True):
                    first_completion = completions[0]
                    response_id = first_completion.metadata.get("id") or (
                        first_completion.inner_content or {}
                    ).get("id")
                    usage = first_completion.metadata.get("usage", None)
                    prompt_tokens = getattr(usage, "prompt_tokens", None)
                    completion_tokens = getattr(usage, "completion_tokens", None)

                    completion_text: str | None = (
                        _messages_to_openai_format(completions)
                        if are_sensitive_events_enabled()
                        else None
                    )

                    finish_reasons: list[str] = [
                        str(completion.finish_reason) for completion in completions
                    ]

                    _set_completion_response(
                        span,
                        completion_text,
                        finish_reasons,
                        response_id or "unknown",
                        prompt_tokens,
                        completion_tokens,
                    )

            return completions

        return wrapper_decorator

    return inner_trace_chat_completion


def trace_text_completion(model_provider: str) -> Callable:
    """Decorator to trace text completion activities."""

    def inner_trace_text_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(*args: Any, **kwargs: Any) -> list[TextContent]:
            prompt: str = kwargs["prompt"]
            settings: PromptExecutionSettings = kwargs["settings"]

            model_name = (
                getattr(settings, "ai_model_id", None)
                or getattr(args[0], "ai_model_id", None)
                or "unknown"
            )

            span = _start_completion_activity(
                TEXT_COMPLETION_OPERATION, model_name, model_provider, prompt, settings
            )

            try:
                completions: list[TextContent] = await completion_func(*args, **kwargs)
            except Exception as exception:
                if span:
                    _set_completion_error(span, exception)
                    span.end()
                raise

            if span and completions:
                with use_span(span, end_on_exit=True):
                    first_completion = completions[0]
                    response_id = first_completion.metadata.get("id") or (
                        first_completion.inner_content or {}
                    ).get("id")
                    usage = first_completion.metadata.get("usage", None)
                    prompt_tokens = getattr(usage, "prompt_tokens", None)
                    completion_tokens = getattr(usage, "completion_tokens", None)

                    completion_text: str | None = (
                        json.dumps([completion.text for completion in completions])
                        if are_sensitive_events_enabled()
                        else None
                    )

                    _set_completion_response(
                        span,
                        completion_text,
                        None,
                        response_id or "unknown",
                        prompt_tokens,
                        completion_tokens,
                    )

            return completions

        return wrapper_decorator

    return inner_trace_text_completion


def _start_completion_activity(
    operation_name: str,
    model_name: str,
    model_provider: str,
    prompt: str | None,
    execution_settings: PromptExecutionSettings | None,
) -> Span | None:
    """Start a text or chat completion activity for a given model."""
    if not are_model_diagnostics_enabled():
        return None

    span = tracer.start_span(f"{operation_name} {model_name}")

    # Set attributes on the span
    span.set_attributes(
        {
            OPERATION: operation_name,
            SYSTEM: model_provider,
            MODEL: model_name,
        }
    )

    # TODO(@glahaye): we'll need to have a way to get these attributes from model
    # providers other than OpenAI (for example if the attributes are named differently)
    if execution_settings:
        attribute = execution_settings.extension_data.get("max_tokens")
        if attribute:
            span.set_attribute(MAX_TOKENS, attribute)

        attribute = execution_settings.extension_data.get("temperature")
        if attribute:
            span.set_attribute(TEMPERATURE, attribute)

        attribute = execution_settings.extension_data.get("top_p")
        if attribute:
            span.set_attribute(TOP_P, attribute)

    if are_sensitive_events_enabled() and prompt:
        span.add_event(PROMPT_EVENT, {PROMPT_EVENT_PROMPT: prompt})

    return span


def _set_completion_response(
    span: Span,
    completion_text: str | None,
    finish_reasons: list[str] | None,
    response_id: str,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
) -> None:
    """Set the a text or chat completion response for a given activity."""
    if not are_model_diagnostics_enabled():
        return

    span.set_attribute(RESPONSE_ID, response_id)

    if finish_reasons:
        span.set_attribute(FINISH_REASON, ",".join(finish_reasons))

    if prompt_tokens:
        span.set_attribute(PROMPT_TOKENS, prompt_tokens)

    if completion_tokens:
        span.set_attribute(COMPLETION_TOKENS, completion_tokens)

    if are_sensitive_events_enabled() and completion_text:
        span.add_event(COMPLETION_EVENT, {COMPLETION_EVENT_COMPLETION: completion_text})


def _set_completion_error(span: Span, error: Exception) -> None:
    """Set an error for a text or chat completion ."""
    if not are_model_diagnostics_enabled():
        return

    span.set_attribute(ERROR_TYPE, str(type(error)))

    span.set_status(StatusCode.ERROR, repr(error))


def _messages_to_openai_format(messages: list[ChatMessageContent]) -> str:
    """Convert a list of ChatMessageContent to a string in the OpenAI format.

    OpenTelemetry recommends formatting the messages in the OpenAI format
    regardless of the actual model being used.
    """
    return json.dumps([message.to_dict() for message in messages])
