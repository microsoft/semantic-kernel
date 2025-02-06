# Copyright (c) Microsoft. All rights reserved.

import functools
from collections.abc import AsyncIterable, Callable
from typing import TYPE_CHECKING, Any

from opentelemetry.trace import get_tracer

from semantic_kernel.utils.experimental_decorator import experimental_function
from semantic_kernel.utils.telemetry.agent_diagnostics import gen_ai_attributes

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent


# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)


@experimental_function
def trace_agent_invocation(invoke_func: Callable) -> Callable:
    """Decorator to trace agent invocation."""
    OPERATION_NAME = "invoke_agent"

    @functools.wraps(invoke_func)
    async def wrapper_decorator(*args: Any, **kwargs: Any) -> AsyncIterable:
        agent: "Agent" = args[0]

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
