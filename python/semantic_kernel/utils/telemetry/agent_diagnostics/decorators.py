# Copyright (c) Microsoft. All rights reserved.

import functools
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import ParamSpec, TypeVar, cast

from opentelemetry.trace import get_tracer

from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.agent_diagnostics import gen_ai_attributes

P = ParamSpec("P")
T = TypeVar("T")

# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)


@experimental
def trace_agent_invocation(invoke_func: Callable[P, AsyncIterable[T]]) -> Callable[P, AsyncIterable[T]]:
    """Decorator to trace agent invocation."""
    OPERATION_NAME = "invoke_agent"

    @functools.wraps(invoke_func)
    async def wrapper_decorator(*args: P.args, **kwargs: P.kwargs) -> AsyncIterable[T]:
        from semantic_kernel.agents.agent import Agent

        agent = cast(Agent, args[0])
        with tracer.start_as_current_span(f"{OPERATION_NAME} {agent.name}") as span:
            span.set_attributes({
                gen_ai_attributes.OPERATION: OPERATION_NAME,
                gen_ai_attributes.AGENT_ID: agent.id,
                gen_ai_attributes.AGENT_NAME: agent.name,
            })

            if agent.description:
                span.set_attribute(gen_ai_attributes.AGENT_DESCRIPTION, agent.description)

            async for response in invoke_func(*args, **kwargs):
                yield response

    # Mark the wrapper decorator as an agent diagnostics decorator
    wrapper_decorator.__agent_diagnostics__ = True  # type: ignore

    return wrapper_decorator


@experimental
def trace_agent_get_response(get_response_func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """Decorator to trace agent invocation."""
    OPERATION_NAME = "invoke_agent"

    @functools.wraps(get_response_func)
    async def wrapper_decorator(*args: P.args, **kwargs: P.kwargs) -> T:
        from semantic_kernel.agents.agent import Agent

        agent = cast(Agent, args[0])

        with tracer.start_as_current_span(f"{OPERATION_NAME} {agent.name}") as span:
            span.set_attributes({
                gen_ai_attributes.OPERATION: OPERATION_NAME,
                gen_ai_attributes.AGENT_ID: agent.id,
                gen_ai_attributes.AGENT_NAME: agent.name,
            })

            if agent.description:
                span.set_attribute(gen_ai_attributes.AGENT_DESCRIPTION, agent.description)

            return await get_response_func(*args, **kwargs)

    # Mark the wrapper decorator as an agent diagnostics decorator
    wrapper_decorator.__agent_diagnostics__ = True  # type: ignore

    return wrapper_decorator
