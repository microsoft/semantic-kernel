# Copyright (c) Microsoft. All rights reserved.

import functools
import json
from collections.abc import AsyncGenerator, Callable
from functools import reduce
from typing import TYPE_CHECKING, Any

from opentelemetry.trace import Span, StatusCode, get_tracer, use_span

from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.experimental_decorator import experimental_function
from semantic_kernel.utils.telemetry.model_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.model_diagnostics_settings import ModelDiagnosticSettings

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase

# Module to instrument GenAI models using OpenTelemetry and OpenTelemetry Semantic Conventions.
# These are experimental features and may change in the future.

# To enable these features, set one of the following environment variables to true:
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE
MODEL_DIAGNOSTICS_SETTINGS = ModelDiagnosticSettings.create()

# Operation names
CHAT_COMPLETION_OPERATION = "chat.completions"
CHAT_STREAMING_COMPLETION_OPERATION = "chat.streaming_completions"
TEXT_COMPLETION_OPERATION = "text.completions"
TEXT_STREAMING_COMPLETION_OPERATION = "text.streaming_completions"

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

            completion_service: "ChatCompletionClientBase" = args[0]
            chat_history: ChatHistory = (
                kwargs.get("chat_history") if kwargs.get("chat_history") is not None else args[1]
            )
            settings: "PromptExecutionSettings" = (
                kwargs.get("settings") if kwargs.get("settings") is not None else args[2]
            )

            with use_span(
                _start_completion_activity(
                    CHAT_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
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

        # Mark the wrapper decorator as a chat completion decorator
        wrapper_decorator.__model_diagnostics_chat_completion__ = True  # type: ignore

        return wrapper_decorator

    return inner_trace_chat_completion


@experimental_function
def trace_streaming_chat_completion(model_provider: str) -> Callable:
    """Decorator to trace streaming chat completion activities.

    Args:
        model_provider (str): The model provider should describe a family of
            GenAI models with specific model identified by ai_model_id. For example,
            model_provider could be "openai" and ai_model_id could be "gpt-3.5-turbo".
            Sometimes the model provider is unknown at runtime, in which case it can be
            set to the most specific known provider. For example, while using local models
            hosted by Ollama, the model provider could be set to "ollama".
    """

    def inner_trace_streaming_chat_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(
            *args: Any, **kwargs: Any
        ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
            if not are_model_diagnostics_enabled():
                # If model diagnostics are not enabled, just return the completion
                async for streaming_chat_message_contents in completion_func(*args, **kwargs):
                    yield streaming_chat_message_contents
                return

            completion_service: "ChatCompletionClientBase" = args[0]
            chat_history: ChatHistory = (
                kwargs.get("chat_history") if kwargs.get("chat_history") is not None else args[1]
            )
            settings: "PromptExecutionSettings" = (
                kwargs.get("settings") if kwargs.get("settings") is not None else args[2]
            )

            all_messages: dict[int, list[StreamingChatMessageContent]] = {}

            with use_span(
                _start_completion_activity(
                    CHAT_STREAMING_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
                    chat_history,
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                try:
                    async for streaming_chat_message_contents in completion_func(*args, **kwargs):
                        for streaming_chat_message_content in streaming_chat_message_contents:
                            choice_index = streaming_chat_message_content.choice_index
                            if choice_index not in all_messages:
                                all_messages[choice_index] = []
                            all_messages[choice_index].append(streaming_chat_message_content)
                        yield streaming_chat_message_contents

                    all_messages_flattened = [
                        reduce(lambda x, y: x + y, messages) for messages in all_messages.values()
                    ]
                    _set_completion_response(current_span, all_messages_flattened)
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        # Mark the wrapper decorator as a streaming chat completion decorator
        wrapper_decorator.__model_diagnostics_streaming_chat_completion__ = True  # type: ignore
        return wrapper_decorator

    return inner_trace_streaming_chat_completion


@experimental_function
def trace_text_completion(model_provider: str) -> Callable:
    """Decorator to trace text completion activities.

    Args:
        model_provider (str): The model provider should describe a family of
            GenAI models with specific model identified by ai_model_id. For example,
            model_provider could be "openai" and ai_model_id could be "gpt-3.5-turbo".
            Sometimes the model provider is unknown at runtime, in which case it can be
            set to the most specific known provider. For example, while using local models
            hosted by Ollama, the model provider could be set to "ollama".
    """

    def inner_trace_text_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(*args: Any, **kwargs: Any) -> list[TextContent]:
            if not are_model_diagnostics_enabled():
                # If model diagnostics are not enabled, just return the completion
                return await completion_func(*args, **kwargs)

            completion_service: "TextCompletionClientBase" = args[0]
            prompt: str = kwargs.get("prompt") if kwargs.get("prompt") is not None else args[1]
            settings: "PromptExecutionSettings" = kwargs["settings"] if kwargs.get("settings") is not None else args[2]

            with use_span(
                _start_completion_activity(
                    TEXT_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
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

        # Mark the wrapper decorator as a text completion decorator
        wrapper_decorator.__model_diagnostics_text_completion__ = True  # type: ignore

        return wrapper_decorator

    return inner_trace_text_completion


@experimental_function
def trace_streaming_text_completion(model_provider: str) -> Callable:
    """Decorator to trace streaming text completion activities.

    Args:
        model_provider (str): The model provider should describe a family of
            GenAI models with specific model identified by ai_model_id. For example,
            model_provider could be "openai" and ai_model_id could be "gpt-3.5-turbo".
            Sometimes the model provider is unknown at runtime, in which case it can be
            set to the most specific known provider. For example, while using local models
            hosted by Ollama, the model provider could be set to "ollama".
    """

    def inner_trace_streaming_text_completion(completion_func: Callable) -> Callable:
        @functools.wraps(completion_func)
        async def wrapper_decorator(*args: Any, **kwargs: Any) -> AsyncGenerator[list["StreamingTextContent"], Any]:
            if not are_model_diagnostics_enabled():
                # If model diagnostics are not enabled, just return the completion
                async for streaming_text_contents in completion_func(*args, **kwargs):
                    yield streaming_text_contents
                return

            completion_service: "TextCompletionClientBase" = args[0]
            prompt: str = kwargs.get("prompt") if kwargs.get("prompt") is not None else args[1]
            settings: "PromptExecutionSettings" = kwargs["settings"] if kwargs.get("settings") is not None else args[2]

            all_text_contents: dict[int, list["StreamingTextContent"]] = {}

            with use_span(
                _start_completion_activity(
                    TEXT_STREAMING_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
                    prompt,
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                try:
                    async for streaming_text_contents in completion_func(*args, **kwargs):
                        for streaming_text_content in streaming_text_contents:
                            choice_index = streaming_text_content.choice_index
                            if choice_index not in all_text_contents:
                                all_text_contents[choice_index] = []
                            all_text_contents[choice_index].append(streaming_text_content)
                        yield streaming_text_contents

                    all_text_contents_flattened = [
                        reduce(lambda x, y: x + y, messages) for messages in all_text_contents.values()
                    ]
                    _set_completion_response(current_span, all_text_contents_flattened)
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        # Mark the wrapper decorator as a streaming text completion decorator
        wrapper_decorator.__model_diagnostics_streaming_text_completion__ = True  # type: ignore
        return wrapper_decorator

    return inner_trace_streaming_text_completion


def _start_completion_activity(
    operation_name: str,
    model_name: str,
    model_provider: str,
    service_url: str | None,
    prompt: str | ChatHistory,
    execution_settings: "PromptExecutionSettings | None",
) -> Span:
    """Start a text or chat completion activity for a given model."""
    span = tracer.start_span(f"{operation_name} {model_name}")

    # Set attributes on the span
    span.set_attributes({
        gen_ai_attributes.OPERATION: operation_name,
        gen_ai_attributes.SYSTEM: model_provider,
        gen_ai_attributes.MODEL: model_name,
    })

    if service_url:
        span.set_attribute(gen_ai_attributes.ADDRESS, service_url)

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
    completions: list[ChatMessageContent]
    | list[TextContent]
    | list[StreamingChatMessageContent]
    | list[StreamingTextContent],
) -> None:
    """Set the a text or chat completion response for a given activity."""
    first_completion = completions[0]

    # Set the response ID
    response_id = first_completion.metadata.get("id")
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
    if isinstance(usage, CompletionUsage):
        if usage.prompt_tokens:
            current_span.set_attribute(gen_ai_attributes.PROMPT_TOKENS, usage.prompt_tokens)
        if usage.completion_tokens:
            current_span.set_attribute(gen_ai_attributes.COMPLETION_TOKENS, usage.completion_tokens)

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


def _messages_to_openai_format(
    messages: list[ChatMessageContent]
    | list[StreamingChatMessageContent]
    | list[TextContent]
    | list[StreamingTextContent],
) -> str:
    """Convert a list of ChatMessageContent to a string in the OpenAI format.

    OpenTelemetry recommends formatting the messages in the OpenAI format
    regardless of the actual model being used.
    """
    return json.dumps([message.to_dict() for message in messages])
