# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from semantic_kernel.agents.runtime.core.agent_id import AgentId
from semantic_kernel.agents.runtime.core.agent_metadata import AgentMetadata
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
@runtime_checkable
class Agent(Protocol):
    """Protocol for an agent."""

    @property
    def metadata(self) -> AgentMetadata:
        """Metadata of the agent."""
        ...

    @property
    def id(self) -> AgentId:
        """ID of the agent."""
        ...

    async def on_message(self, message: Any, ctx: MessageContext) -> Any:
        """Message handler for the agent. This should only be called by the runtime, not by other agents.

        Args:
            message (Any): Received message. Type is one of the types in `subscriptions`.
            ctx (MessageContext): Context of the message.

        Returns:
            Any: Response to the message. Can be None.

        Raises:
            asyncio.CancelledError: If the message was cancelled.
            CantHandleException: If the agent cannot handle the message.
        """
        ...

    async def save_state(self) -> Mapping[str, Any]:
        """Save the state of the agent. The result must be JSON serializable."""
        ...

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """Load in the state of the agent obtained from `save_state`.

        Args:
            state (Mapping[str, Any]): State of the agent. Must be JSON serializable.
        """
        ...

    async def close(self) -> None:
        """Called when the runtime is closed."""
        ...
