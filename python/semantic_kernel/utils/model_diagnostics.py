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

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Span

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent

# Activity tags
_SYSTEM = "gen_ai.system"
_OPERATION = "gen_ai.operation.name"
_MODEL = "gen_ai.request.model"
_MAX_TOKEN = "gen_ai.request.max_tokens"
_TEMPERATURE = "gen_ai.request.temperature"
_TOP_P = "gen_ai.request.top_p"
_RESPONSE_ID = "gen_ai.response.id"
_FINISH_REASON = "gen_ai.response.finish_reason"
_PROMPT_TOKEN = "gen_ai.response.prompt_tokens"
_COMPLETION_TOKEN = "gen_ai.response.completion_tokens"

# Activity events
PROMPT_EVENT_PROMPT = "gen_ai.prompt"
COMPLETION_EVENT_COMPLETION = "gen_ai.completion"

_enable_diagnostics = os.getenv("SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS",
                                "false").lower() in ("true", "1", "t")

_enable_sensitive_events = os.getenv("SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE",
                                     "false").lower() in ("true", "1", "t")

if _enable_diagnostics or _enable_sensitive_events:
    # Configure OpenTelemetry to use Azure Monitor with the 
    # APPLICATIONINSIGHTS_CONNECTION_STRING environment variable.
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        configure_azure_monitor(connection_string=connection_string)

# Sets the global default tracer provider
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


def start_completion_activity(model_name: str, model_provider: str, prompt: str,
                              execution_settings: Optional[PromptExecutionSettings]) -> Optional[Span]:
    """Start a text completion activity for a given model."""
    if not are_model_diagnostics_enabled():
        return None

    operation_name: str = "chat.completions" if isinstance(prompt, ChatHistory) else "text.completions"

    span = tracer.start_span(f"{operation_name} {model_name}")

    # Set attributes on the span
    span.set_attributes({
        _OPERATION: operation_name,
        _SYSTEM: model_provider,
        _MODEL: model_name,
    })

    if execution_settings is not None:
        span.set_attributes({
            _MAX_TOKEN: str(execution_settings.extension_data.get("max_tokens")),
            _TEMPERATURE: str(execution_settings.extension_data.get("temperature")),
            _TOP_P: str(execution_settings.extension_data.get("top_p")),
        })

    if are_sensitive_events_enabled():
        span.add_event(PROMPT_EVENT_PROMPT, {PROMPT_EVENT_PROMPT: prompt})

    return span


def set_completion_response(span: Span, completions: list[ChatMessageContent], finish_reasons: list[str],
                            response_id: str, prompt_tokens: Optional[int] = None,
                            completion_tokens: Optional[int] = None) -> None:
    """Set the text completion response for a given activity."""
    if not are_model_diagnostics_enabled():
        return

    if prompt_tokens:
        span.set_attribute(_PROMPT_TOKEN, prompt_tokens)

    if completion_tokens:
        span.set_attribute(_COMPLETION_TOKEN, completion_tokens)

    if finish_reasons:
        span.set_attribute(_FINISH_REASON, ",".join(finish_reasons))

    span.set_attribute(_RESPONSE_ID, response_id)

    if are_sensitive_events_enabled() and len(completions) > 0:
        span.add_event(COMPLETION_EVENT_COMPLETION,
                       {COMPLETION_EVENT_COMPLETION: _messages_to_openai_format(completions)})


def _messages_to_openai_format(chat_history: list[ChatMessageContent]) -> str:
    formatted_messages = []
    for message in chat_history:
        message_dict = {
            "role": message.role,
            "content": json.dumps(message.content)
        }
        if any(isinstance(item, FunctionCallContent) for item in message.items):
            message_dict["tool_calls"] = _tool_calls_to_openai_format(message.items)
        formatted_messages.append(json.dumps(message_dict))

    return f"[{', \n'.join(formatted_messages)}]"


def _tool_calls_to_openai_format(items: list[ITEM_TYPES]) -> str:
    tool_calls: list[str] = []
    for item in items:
        if isinstance(item, FunctionCallContent):
            tool_call = {
                "id": item.id,
                "function": {
                    "arguments": json.dumps(item.arguments),
                    "name": item.function_name
                },
                "type": "function"
            }
            tool_calls.append(json.dumps(tool_call))
    return f"[{', '.join(tool_calls)}]"