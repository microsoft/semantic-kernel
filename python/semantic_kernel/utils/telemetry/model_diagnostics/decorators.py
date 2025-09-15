# Copyright (c) Microsoft. All rights reserved.

import functools
import json
import logging
from collections.abc import AsyncGenerator, Callable
from functools import reduce
from typing import TYPE_CHECKING, Any, ClassVar

from opentelemetry.trace import Span, StatusCode, get_tracer, use_span

from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.feature_stage_decorator import experimental
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
MODEL_DIAGNOSTICS_SETTINGS = ModelDiagnosticSettings()

# Operation names
CHAT_COMPLETION_OPERATION = "chat.completions"
CHAT_STREAMING_COMPLETION_OPERATION = "chat.streaming_completions"
TEXT_COMPLETION_OPERATION = "text.completions"
TEXT_STREAMING_COMPLETION_OPERATION = "text.streaming_completions"


# We're recording multiple events for the chat history, some of them are emitted within (hundreds of)
# nanoseconds of each other. The default timestamp resolution is not high enough to guarantee unique
# timestamps for each message. Also Azure Monitor truncates resolution to microseconds and some other
# backends truncate to milliseconds.
#
# But we need to give users a way to restore chat message order, so we're incrementing the timestamp
# by 1 microsecond for each message.
#
# This is a workaround, we'll find a generic and better solution - see
# https://github.com/open-telemetry/semantic-conventions/issues/1701
class ChatHistoryMessageTimestampFilter(logging.Filter):
    """A filter to increment the timestamp of INFO logs by 1 microsecond."""

    INDEX_KEY: ClassVar[str] = "CHAT_MESSAGE_INDEX"

    def filter(self, record: logging.LogRecord) -> bool:
        """Increment the timestamp of INFO logs by 1 microsecond."""
        if hasattr(record, self.INDEX_KEY):
            idx = getattr(record, self.INDEX_KEY)
            record.created += idx * 1e-6
        return True


# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)

logger = logging.getLogger(__name__)
logger.addFilter(ChatHistoryMessageTimestampFilter())


@experimental
def are_model_diagnostics_enabled() -> bool:
    """Check if model diagnostics are enabled.

    Model diagnostics are enabled if either diagnostic is enabled or diagnostic with sensitive events is enabled.
    """
    return (
        MODEL_DIAGNOSTICS_SETTINGS.enable_otel_diagnostics
        or MODEL_DIAGNOSTICS_SETTINGS.enable_otel_diagnostics_sensitive
    )


@experimental
def are_sensitive_events_enabled() -> bool:
    """Check if sensitive events are enabled.

    Sensitive events are enabled if the diagnostic with sensitive events is enabled.
    """
    return MODEL_DIAGNOSTICS_SETTINGS.enable_otel_diagnostics_sensitive


@experimental
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
            chat_history: ChatHistory = kwargs.get("chat_history") or args[1]  # type: ignore
            settings: "PromptExecutionSettings" = kwargs.get("settings") or args[2]  # type: ignore

            with use_span(
                _get_completion_span(
                    CHAT_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                _set_completion_input(model_provider, chat_history)
                try:
                    completions: list[ChatMessageContent] = await completion_func(*args, **kwargs)
                    _set_completion_response(current_span, completions, model_provider)
                    return completions
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        # Mark the wrapper decorator as a chat completion decorator
        wrapper_decorator.__model_diagnostics_chat_completion__ = True  # type: ignore

        return wrapper_decorator

    return inner_trace_chat_completion


@experimental
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
            chat_history: ChatHistory = kwargs.get("chat_history") or args[1]  # type: ignore
            settings: "PromptExecutionSettings" = kwargs.get("settings") or args[2]  # type: ignore

            all_messages: dict[int, list[StreamingChatMessageContent]] = {}

            with use_span(
                _get_completion_span(
                    CHAT_STREAMING_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                _set_completion_input(model_provider, chat_history)
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
                    _set_completion_response(current_span, all_messages_flattened, model_provider)
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        # Mark the wrapper decorator as a streaming chat completion decorator
        wrapper_decorator.__model_diagnostics_streaming_chat_completion__ = True  # type: ignore
        return wrapper_decorator

    return inner_trace_streaming_chat_completion


@experimental
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
            prompt: str = kwargs.get("prompt") if kwargs.get("prompt") is not None else args[1]  # type: ignore
            settings: "PromptExecutionSettings" = kwargs["settings"] if kwargs.get("settings") is not None else args[2]

            with use_span(
                _get_completion_span(
                    TEXT_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                _set_completion_input(model_provider, prompt)
                try:
                    completions: list[TextContent] = await completion_func(*args, **kwargs)
                    _set_completion_response(current_span, completions, model_provider)
                    return completions
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        # Mark the wrapper decorator as a text completion decorator
        wrapper_decorator.__model_diagnostics_text_completion__ = True  # type: ignore

        return wrapper_decorator

    return inner_trace_text_completion


@experimental
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
            prompt: str = kwargs.get("prompt") if kwargs.get("prompt") is not None else args[1]  # type: ignore
            settings: "PromptExecutionSettings" = kwargs["settings"] if kwargs.get("settings") is not None else args[2]

            all_text_contents: dict[int, list["StreamingTextContent"]] = {}

            with use_span(
                _get_completion_span(
                    TEXT_STREAMING_COMPLETION_OPERATION,
                    completion_service.ai_model_id,
                    model_provider,
                    completion_service.service_url(),
                    settings,
                ),
                end_on_exit=True,
            ) as current_span:
                _set_completion_input(model_provider, prompt)
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
                    _set_completion_response(current_span, all_text_contents_flattened, model_provider)
                except Exception as exception:
                    _set_completion_error(current_span, exception)
                    raise

        # Mark the wrapper decorator as a streaming text completion decorator
        wrapper_decorator.__model_diagnostics_streaming_text_completion__ = True  # type: ignore
        return wrapper_decorator

    return inner_trace_streaming_text_completion


def _get_completion_span(
    operation_name: str,
    model_name: str,
    model_provider: str,
    service_url: str | None,
    execution_settings: "PromptExecutionSettings | None",
) -> Span:
    """Start a text or chat completion span for a given model.

    Note that `start_span` doesn't make the span the current span.
    Use `use_span` to make it the current span as a context manager.
    """
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
        attribute_name_map = {
            "seed": gen_ai_attributes.SEED,
            "encoding_formats": gen_ai_attributes.ENCODING_FORMATS,
            "frequency_penalty": gen_ai_attributes.FREQUENCY_PENALTY,
            "max_tokens": gen_ai_attributes.MAX_TOKENS,
            "stop_sequences": gen_ai_attributes.STOP_SEQUENCES,
            "temperature": gen_ai_attributes.TEMPERATURE,
            "top_k": gen_ai_attributes.TOP_K,
            "top_p": gen_ai_attributes.TOP_P,
        }
        for attribute_name, attribute_key in attribute_name_map.items():
            attribute = execution_settings.extension_data.get(attribute_name)
            if attribute:
                span.set_attribute(attribute_key, attribute)

    return span


def _set_completion_input(
    model_provider: str,
    prompt: str | ChatHistory,
) -> None:
    """Set the input for a text or chat completion.

    The logs will be associated to the current span.
    """
    if are_sensitive_events_enabled():
        if isinstance(prompt, ChatHistory):
            for idx, message in enumerate(prompt.messages):
                event_name = gen_ai_attributes.ROLE_EVENT_MAP.get(message.role)
                if event_name:
                    logger.info(
                        json.dumps(message.to_dict()),
                        extra={
                            gen_ai_attributes.EVENT_NAME: event_name,
                            gen_ai_attributes.SYSTEM: model_provider,
                            ChatHistoryMessageTimestampFilter.INDEX_KEY: idx,
                        },
                    )
        else:
            logger.info(
                prompt,
                extra={
                    gen_ai_attributes.EVENT_NAME: gen_ai_attributes.PROMPT,
                    gen_ai_attributes.SYSTEM: model_provider,
                },
            )


def _set_completion_response(
    current_span: Span,
    completions: list[ChatMessageContent]
    | list[TextContent]
    | list[StreamingChatMessageContent]
    | list[StreamingTextContent],
    model_provider: str,
) -> None:
    """Set the a text or chat completion response for a given span."""
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
            current_span.set_attribute(gen_ai_attributes.INPUT_TOKENS, usage.prompt_tokens)
        if usage.completion_tokens:
            current_span.set_attribute(gen_ai_attributes.OUTPUT_TOKENS, usage.completion_tokens)

    # Set the completion event
    if are_sensitive_events_enabled():
        for completion in completions:
            full_response: dict[str, Any] = {
                "message": completion.to_dict(),
            }

            if isinstance(completion, ChatMessageContent):
                full_response["finish_reason"] = completion.finish_reason
            if isinstance(completion, StreamingContentMixin):
                full_response["index"] = completion.choice_index

            logger.info(
                json.dumps(full_response),
                extra={
                    gen_ai_attributes.EVENT_NAME: gen_ai_attributes.CHOICE,
                    gen_ai_attributes.SYSTEM: model_provider,
                },
            )


def _set_completion_error(span: Span, error: Exception) -> None:
    """Set an error for a text or chat completion ."""
    span.set_attribute(gen_ai_attributes.ERROR_TYPE, str(type(error)))
    span.set_status(StatusCode.ERROR, repr(error))
