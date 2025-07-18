# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, ClassVar

from semantic_kernel.agents.runtime.core.agent_type import AgentType
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class SubscriptionInstantiationContext:
    """Context manager for subscription instantiation."""

    def __init__(self) -> None:
        """Prevent instantiation of SubscriptionInstantiationContext."""
        raise RuntimeError(
            "SubscriptionInstantiationContext cannot be instantiated. It is a static class that provides context "
            "management for subscription instantiation."
        )

    _SUBSCRIPTION_CONTEXT_VAR: ClassVar[ContextVar[AgentType]] = ContextVar("_SUBSCRIPTION_CONTEXT_VAR")

    @classmethod
    @contextmanager
    def populate_context(cls, ctx: AgentType) -> Generator[None, Any, None]:
        """Populate the context with the agent type."""
        token = SubscriptionInstantiationContext._SUBSCRIPTION_CONTEXT_VAR.set(ctx)
        try:
            yield
        finally:
            SubscriptionInstantiationContext._SUBSCRIPTION_CONTEXT_VAR.reset(token)

    @classmethod
    def agent_type(cls) -> AgentType:
        """Get the agent type from the context."""
        try:
            return cls._SUBSCRIPTION_CONTEXT_VAR.get()
        except LookupError as e:
            raise RuntimeError(
                "SubscriptionInstantiationContext.runtime() must be called within an instantiation context such as "
                "when the AgentRuntime is instantiating an agent. Mostly likely this was caused by directly "
                "instantiating an agent instead of using the AgentRuntime to do so."
            ) from e
