# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, ClassVar

from semantic_kernel.agents.runtime.core.agent_id import AgentId
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AgentInstantiationContext:
    """A static class that provides context for agent instantiation.

    This static class can be used to access the current runtime and agent ID
    during agent instantiation -- inside the factory function or the agent's
    class constructor.
    """

    def __init__(self) -> None:
        """Instantiate the AgentInstantiationContext class."""
        raise RuntimeError(
            "AgentInstantiationContext cannot be instantiated. It is a static class that provides context management "
            "for agent instantiation."
        )

    _AGENT_INSTANTIATION_CONTEXT_VAR: ClassVar[ContextVar[tuple[CoreRuntime, AgentId]]] = ContextVar(
        "_AGENT_INSTANTIATION_CONTEXT_VAR"
    )

    @classmethod
    @contextmanager
    def populate_context(cls, ctx: tuple[CoreRuntime, AgentId]) -> Generator[None, Any, None]:
        """Populate the context with the current runtime and agent ID."""
        token = AgentInstantiationContext._AGENT_INSTANTIATION_CONTEXT_VAR.set(ctx)
        try:
            yield
        finally:
            AgentInstantiationContext._AGENT_INSTANTIATION_CONTEXT_VAR.reset(token)

    @classmethod
    def current_runtime(cls) -> CoreRuntime:
        """Get the current runtime."""
        try:
            return cls._AGENT_INSTANTIATION_CONTEXT_VAR.get()[0]
        except LookupError as e:
            raise RuntimeError(
                "AgentInstantiationContext.runtime() must be called within an instantiation context such as when the "
                "AgentRuntime is instantiating an agent. Mostly likely this was caused by directly instantiating an "
                "agent instead of using the AgentRuntime to do so."
            ) from e

    @classmethod
    def current_agent_id(cls) -> AgentId:
        """Get the current agent ID."""
        try:
            return cls._AGENT_INSTANTIATION_CONTEXT_VAR.get()[1]
        except LookupError as e:
            raise RuntimeError(
                "AgentInstantiationContext.agent_id() must be called within an instantiation context such as when the "
                "AgentRuntime is instantiating an agent. Mostly likely this was caused by directly instantiating an "
                "agent instead of using the AgentRuntime to do so."
            ) from e
