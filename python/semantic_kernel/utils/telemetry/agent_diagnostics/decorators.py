# Copyright (c) Microsoft. All rights reserved.

import functools
from collections.abc import AsyncIterable, Callable
from typing import TYPE_CHECKING, Any

from opentelemetry.trace import get_tracer

from semantic_kernel.utils.experimental_decorator import experimental_function

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent


# Creates a tracer from the global tracer provider
tracer = get_tracer(__name__)


@experimental_function
def trace_agent_invocation(invoke_func: Callable) -> Callable:
    """Decorator to trace agent invocation."""

    @functools.wraps(invoke_func)
    async def wrapper_decorator(*args: Any, **kwargs: Any) -> AsyncIterable:
        agent: "Agent" = args[0]

        with tracer.start_as_current_span(agent.name):
            async for response in invoke_func(*args, **kwargs):
                yield response

    # Mark the wrapper decorator as an agent diagnostics decorator
    wrapper_decorator.__agent_diagnostics__ = True  # type: ignore

    return wrapper_decorator
