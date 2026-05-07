# Copyright (c) Microsoft. All rights reserved.

import functools
import json
from collections.abc import AsyncIterable, Awaitable, Callable
from functools import reduce
from typing import ParamSpec, cast

from opentelemetry.trace import Span, StatusCode, get_tracer

from semantic_kernel.agents.agent import Agent, AgentResponseItem
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.agent_diagnostics import gen_ai_attributes
from semantic_kernel.utils.telemetry.model_diagnostics.model_diagnostics_settings import ModelDiagnosticSettings

# Module to instrument GenAI agents using OpenTelemetry and OpenTelemetry Semantic Conventions.
# These are experimental features and may change in the future.

# To enable these features, set one of the following environment variables to true:
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS
#    SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE
# We are re-using the model diagnostic settings to control the instrumentation of agents
# because it makes sense to have a system wide setting for diagnostics. The name "model"
# is a legacy name because the concept of agent was not yet introduced when the settings were created.
MODEL_DIAGNOSTICS_SETTINGS = ModelDiagnosticSettings()

P = ParamSpec("P")

# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)

OPERATION_NAME = "invoke_agent"


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
def trace_agent_get_response(
    get_response_func: Callable[P, Awaitable[AgentResponseItem[ChatMessageContent]]],
) -> Callable[P, Awaitable[AgentResponseItem[ChatMessageContent]]]:
    """Decorator to trace agent invocation."""

    @functools.wraps(get_response_func)
    async def wrapper_decorator(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        if not are_model_diagnostics_enabled():
            # If model diagnostics are not enabled, just return the responses
            return await get_response_func(*args, **kwargs)

        agent = cast(Agent, args[0])
        messages = args[1] if len(args) > 1 else None

        with _start_as_current_span(agent) as span:
            try:
                _set_agent_invocation_input(span, messages)  # type: ignore
                response = await get_response_func(*args, **kwargs)
                _set_agent_invocation_output(span, [response.message])
                return response
            except Exception as e:
                _set_agent_invocation_error(span, e)
                raise

    # Mark the wrapper decorator as an agent diagnostics decorator
    wrapper_decorator.__agent_diagnostics__ = True  # type: ignore

    return wrapper_decorator


@experimental
def trace_agent_invocation(
    invoke_func: Callable[P, AsyncIterable[AgentResponseItem[ChatMessageContent]]],
) -> Callable[P, AsyncIterable[AgentResponseItem[ChatMessageContent]]]:
    """Decorator to trace agent invocation."""

    @functools.wraps(invoke_func)
    async def wrapper_decorator(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        if not are_model_diagnostics_enabled():
            # If model diagnostics are not enabled, just return the responses
            async for response in invoke_func(*args, **kwargs):
                yield response
            return

        agent = cast(Agent, args[0])
        messages = args[1] if len(args) > 1 else None

        with _start_as_current_span(agent) as current_span:
            _set_agent_invocation_input(current_span, messages)  # type: ignore
            try:
                responses: list[ChatMessageContent] = []
                async for response in invoke_func(*args, **kwargs):
                    responses.append(response.message)
                    yield response
                _set_agent_invocation_output(current_span, responses)
            except Exception as e:
                _set_agent_invocation_error(current_span, e)
                raise

    # Mark the wrapper decorator as an agent diagnostics decorator
    wrapper_decorator.__agent_diagnostics__ = True  # type: ignore

    return wrapper_decorator


@experimental
def trace_agent_streaming_invocation(
    invoke_func: Callable[P, AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]],
) -> Callable[P, AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]]:
    """Decorator to trace agent streaming invocation."""

    @functools.wraps(invoke_func)
    async def wrapper_decorator(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        if not are_model_diagnostics_enabled():
            # If model diagnostics are not enabled, just return the responses
            async for chunk in invoke_func(*args, **kwargs):
                yield chunk
            return

        agent = cast(Agent, args[0])
        messages = args[1] if len(args) > 1 else None

        with _start_as_current_span(agent) as current_span:
            _set_agent_invocation_input(current_span, messages)  # type: ignore
            try:
                chunks: list[StreamingChatMessageContent] = []
                async for chunk in invoke_func(*args, **kwargs):
                    chunks.append(chunk.message)
                    yield chunk
                # Concatenate the streaming chunks
                if chunks:
                    response = reduce(lambda x, y: x + y, chunks)
                    _set_agent_invocation_output(current_span, [response])
                else:
                    _set_agent_invocation_output(current_span, [])
            except Exception as e:
                _set_agent_invocation_error(current_span, e)
                raise

    # Mark the wrapper decorator as an agent diagnostics decorator
    wrapper_decorator.__agent_diagnostics__ = True  # type: ignore

    return wrapper_decorator


def _start_as_current_span(agent: Agent):
    """Starts a span for the given agent.

    Args:
        agent (Agent): The agent for which to start the span.

    Returns:
        Span: The started span as a context manager.
    """
    attributes = {
        gen_ai_attributes.OPERATION: OPERATION_NAME,
        gen_ai_attributes.AGENT_ID: agent.id,
        gen_ai_attributes.AGENT_NAME: agent.name,
    }

    if agent.description:
        attributes[gen_ai_attributes.AGENT_DESCRIPTION] = agent.description

    if agent.kernel.plugins:
        # This will only capture the tools that are available in the kernel at the time of agent creation.
        # If the agent is invoked with another kernel instance, the tools in that kernel will not be captured.
        from semantic_kernel.connectors.ai.function_calling_utils import (
            kernel_function_metadata_to_function_call_format,
        )

        tool_definitions = [
            kernel_function_metadata_to_function_call_format(metadata)
            for metadata in agent.kernel.get_full_list_of_function_metadata()
        ]
        attributes[gen_ai_attributes.AGENT_TOOL_DEFINITIONS] = json.dumps(tool_definitions)

    return tracer.start_as_current_span(f"{OPERATION_NAME} {agent.name}", attributes=attributes)


def _set_agent_invocation_input(
    current_span: Span,
    messages: str | ChatMessageContent | list[str | ChatMessageContent] | None,
) -> None:
    """Set the agent input attributes in the span."""
    if are_sensitive_events_enabled():
        parsed_messages = _parse_agent_invocation_messages(messages)
        current_span.set_attribute(
            gen_ai_attributes.AGENT_INVOCATION_INPUT,
            json.dumps([message.to_dict() for message in parsed_messages]),
        )


def _set_agent_invocation_output(current_span: Span, response: list[ChatMessageContent]) -> None:
    """Set the agent output attributes in the span."""
    if are_sensitive_events_enabled():
        current_span.set_attribute(
            gen_ai_attributes.AGENT_INVOCATION_OUTPUT,
            json.dumps([message.to_dict() for message in response]),
        )


def _set_agent_invocation_error(current_span: Span, error: Exception) -> None:
    """Set the agent error attributes in the span."""
    current_span.set_attribute(gen_ai_attributes.ERROR_TYPE, type(error).__name__)
    current_span.set_status(StatusCode.ERROR, repr(error))


def _parse_agent_invocation_messages(
    messages: str | ChatMessageContent | list[str | ChatMessageContent] | None,
) -> list[ChatMessageContent]:
    """Parse the agent invocation messages into a list of ChatMessageContent."""
    if not messages:
        return []

    if isinstance(messages, str):
        return [ChatMessageContent(role=AuthorRole.USER, content=messages)]
    if isinstance(messages, ChatMessageContent):
        return [messages]
    if isinstance(messages, list):
        return [
            msg if isinstance(msg, ChatMessageContent) else ChatMessageContent(role=AuthorRole.USER, content=msg)
            for msg in messages
        ]

    return []
