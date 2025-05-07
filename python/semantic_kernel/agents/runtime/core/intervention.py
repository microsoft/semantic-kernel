# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Protocol, final

from semantic_kernel.agents.runtime.core.agent_id import AgentId
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.utils.feature_stage_decorator import experimental

__all__ = [
    "DefaultInterventionHandler",
    "DropMessage",
    "InterventionHandler",
]


@experimental
@final
class DropMessage:
    """Marker type for signalling that a message should be dropped by an intervention handler.

    The type itself should be returned from the handler.
    """

    ...


@experimental
class InterventionHandler(Protocol):
    """An intervention handler is a class that can be used to modify, log or drop messages.

    These messages are being processed by the :class:`autogen_core.base.AgentRuntime`.

    The handler is called when the message is submitted to the runtime.

    Currently the only runtime which supports this is the :class:`autogen_core.base.SingleThreadedAgentRuntime`.

    Note: Returning None from any of the intervention handler methods will result in a warning being issued and treated
    as "no change". If you intend to drop a message, you should return :class:`DropMessage` explicitly.
    """

    async def on_send(
        self, message: Any, *, message_context: MessageContext, recipient: AgentId
    ) -> Any | type[DropMessage]:
        """Called when a message is submitted to the AgentRuntime."""
        ...

    async def on_publish(self, message: Any, *, message_context: MessageContext) -> Any | type[DropMessage]:
        """Called when a message is published to the AgentRuntime."""
        ...

    async def on_response(self, message: Any, *, sender: AgentId, recipient: AgentId | None) -> Any | type[DropMessage]:
        """Called when a response is received by the AgentRuntime from an Agent's message handler returning a value."""
        ...


@experimental
class DefaultInterventionHandler(InterventionHandler):
    """Simple class that provides a default implementation for all intervention handler methods.

    Simply returns the message unchanged. Allows for easy
    subclassing to override only the desired methods.
    """

    async def on_send(
        self, message: Any, *, message_context: MessageContext, recipient: AgentId
    ) -> Any | type[DropMessage]:
        """Called when a message is submitted to the AgentRuntime."""
        return message

    async def on_publish(self, message: Any, *, message_context: MessageContext) -> Any | type[DropMessage]:
        """Called when a message is published to the AgentRuntime."""
        return message

    async def on_response(self, message: Any, *, sender: AgentId, recipient: AgentId | None) -> Any | type[DropMessage]:
        """Called when a response is received by the AgentRuntime from an Agent's message handler returning a value."""
        return message
