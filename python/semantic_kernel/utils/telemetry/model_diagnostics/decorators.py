# Copyright (c) Microsoft. All rights reserved.

import functools
import json
from collections.abc import Callable
from typing import Any

from opentelemetry.trace import Span, StatusCode, get_tracer, use_span

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.experimental_decorator import experimental_function
from semantic_kernel.utils.telemetry.model_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.model_diagnostics_settings import ModelDiagnosticSettings

# Module to instrument GenAI models using OpenTelemetry and OpenTelemetry Semantic Conventions.
# These are experimental features and may change in the future.

# To enable these features, set one of the following environment variables to true:
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE
MODEL_DIAGNOSTICS_SETTINGS = ModelDiagnosticSettings.create()

# Operation names
CHAT_COMPLETION_OPERATION = "chat.completions"
TEXT_COMPLETION_OPERATION = "text.completions"

# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)


@experimental_function
def are_model_diagnostics_enabled() -> bool:
    """Check if model diagnostics are enabled.

    Model diagnostics are enabled if either diagnostic is enabled or diagnostic with sensitive events is enabled.
    """
    return (
        MODEL_DIAGNOSTICS_SETTINGS.enable_otel_diagnostics
        or MODEL_DIAGNOSTICS_SETTINGS.enable_otel_diagnostics_sensitive
    )


@experimental_function
def are_sensitive_events_enabled() -> bool:
    """Check if sensitive events are enabled.

    Sensitive events are enabled if the diagnostic with sensitive events is enabled.
    """
    return MODEL_DIAGNOSTICS_SETTINGS.enable_otel_diagnostics_sensitive


@experimental_function
def trace_chat_completion(model_provider: str) -> Callable:
    """Decorator to trace chat completion activities.

    Args:
        model_provider (str): The model provider should describe a family of
            GenAI models with specific model identified by ai_model_id. For example,
            model_provider could be "openai" and ai_model_id could be "gpt-3.5-turbo".
            Sometimes the model provider is unknown at runtime, in which case it can be
            set to the most specific known provider. For example, while using local models
            hosted by Ollama, the model provider could be set to "ollama".
    """

    def inner_trace_chat_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(*args: Any, **kwargs: Any) -> list[ChatMessageContent]:
            if not are_model_diagnostics_enabled():
                # If model diagnostics are not enabled, just return the completion
                return await completion_func(*args, **kwargs)

            completion_service: ChatCompletionClientBase = args[0]
            chat_history: ChatHistory = kwargs["chat_history"]
            settings: PromptExecutionSettings = kwargs["settings"]

            with use_span(
                _start_completion_activity(
                    CHAT_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    chat_history,
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                try:
                    completions: list[ChatMessageContent] = await completion_func(*args, **kwargs)
                    _set_completion_response(current_span, completions)
                    return completions
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        return wrapper_decorator

    return inner_trace_chat_completion


@experimental_function
def trace_text_completion(model_provider: str) -> Callable:
    """Decorator to trace text completion activities."""

    def inner_trace_text_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(*args: Any, **kwargs: Any) -> list[TextContent]:
            if not are_model_diagnostics_enabled():
                # If model diagnostics are not enabled, just return the completion
                return await completion_func(*args, **kwargs)

            completion_service: TextCompletionClientBase = args[0]
            prompt: str = kwargs["prompt"]
            settings: PromptExecutionSettings = kwargs["settings"]

            with use_span(
                _start_completion_activity(
                    TEXT_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    prompt,
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                try:
                    completions: list[TextContent] = await completion_func(*args, **kwargs)
                    _set_completion_response(current_span, completions)
                    return completions
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        return wrapper_decorator

    return inner_trace_text_completion


def _start_completion_activity(
    operation_name: str,
    model_name: str,
    model_provider: str,
    prompt: str | ChatHistory,
    execution_settings: PromptExecutionSettings | None,
) -> Span:
    """Start a text or chat completion activity for a given model."""
    span = tracer.start_span(f"{operation_name} {model_name}")

    # Set attributes on the span
    span.set_attributes({
        gen_ai_attributes.OPERATION: operation_name,
        gen_ai_attributes.SYSTEM: model_provider,
        gen_ai_attributes.MODEL: model_name,
    })

    # TODO(@glahaye): we'll need to have a way to get these attributes from model
    # providers other than OpenAI (for example if the attributes are named differently)
    if execution_settings:
        attribute = execution_settings.extension_data.get("max_tokens")
        if attribute:
            span.set_attribute(gen_ai_attributes.MAX_TOKENS, attribute)

        attribute = execution_settings.extension_data.get("temperature")
        if attribute:
            span.set_attribute(gen_ai_attributes.TEMPERATURE, attribute)

        attribute = execution_settings.extension_data.get("top_p")
        if attribute:
            span.set_attribute(gen_ai_attributes.TOP_P, attribute)

    if are_sensitive_events_enabled():
        if isinstance(prompt, ChatHistory):
            prompt = _messages_to_openai_format(prompt.messages)
        span.add_event(gen_ai_attributes.PROMPT_EVENT, {gen_ai_attributes.PROMPT_EVENT_PROMPT: prompt})

    return span


def _set_completion_response(
    current_span: Span,
    completions: list[ChatMessageContent] | list[TextContent],
) -> None:
    """Set the a text or chat completion response for a given activity."""
    first_completion = completions[0]

    # Set the response ID
    response_id = first_completion.metadata.get("id") or (first_completion.inner_content or {}).get("id")
    if response_id:
        current_span.set_attribute(gen_ai_attributes.RESPONSE_ID, response_id)

    # Set the finish reason
    finish_reasons = [
        str(completion.finish_reason) for completion in completions if isinstance(completion, ChatMessageContent)
    ]
    if finish_reasons:
        current_span.set_attribute(gen_ai_attributes.FINISH_REASON, ",".join(finish_reasons))

    # Set usage attributes
    usage = first_completion.metadata.get("usage", None)

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    if prompt_tokens:
        current_span.set_attribute(gen_ai_attributes.PROMPT_TOKENS, prompt_tokens)

    completion_tokens = getattr(usage, "completion_tokens", None)
    if completion_tokens:
        current_span.set_attribute(gen_ai_attributes.COMPLETION_TOKENS, completion_tokens)

    # Set the completion event
    if are_sensitive_events_enabled():
        completion_text: str = _messages_to_openai_format(completions)
        current_span.add_event(
            gen_ai_attributes.COMPLETION_EVENT, {gen_ai_attributes.COMPLETION_EVENT_COMPLETION: completion_text}
        )


def _set_completion_error(span: Span, error: Exception) -> None:
    """Set an error for a text or chat completion ."""
    span.set_attribute(gen_ai_attributes.ERROR_TYPE, str(type(error)))
    span.set_status(StatusCode.ERROR, repr(error))


def _messages_to_openai_format(messages: list[ChatMessageContent] | list[TextContent]) -> str:
    """Convert a list of ChatMessageContent to a string in the OpenAI format.

    OpenTelemetry recommends formatting the messages in the OpenAI format
    regardless of the actual model being used.
    """
    return json.dumps([message.to_dict() for message in messages])
