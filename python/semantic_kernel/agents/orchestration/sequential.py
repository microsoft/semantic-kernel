# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Awaitable, Callable

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.orchestration.agent_actor_base import AgentActorBase
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias, OrchestrationBase, TIn, TOut
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import RoutedAgent, message_handler
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


logger: logging.Logger = logging.getLogger(__name__)


class SequentialRequestMessage(KernelBaseModel):
    """A request message type for concurrent agents."""

    body: DefaultTypeAlias


class SequentialResultMessage(KernelBaseModel):
    """A result message type for concurrent agents."""

    body: ChatMessageContent


class SequentialAgentActor(AgentActorBase):
    """A agent actor for sequential agents that process tasks."""

    def __init__(
        self,
        agent: Agent,
        internal_topic_type: str,
        next_agent_type: str,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
    ) -> None:
        """Initialize the agent actor."""
        self._next_agent_type = next_agent_type
        super().__init__(
            agent=agent,
            internal_topic_type=internal_topic_type,
            agent_response_callback=agent_response_callback,
        )

    @message_handler
    async def _handle_message(self, message: SequentialRequestMessage, ctx: MessageContext) -> None:
        """Handle a message."""
        logger.debug(f"Sequential actor (Actor ID: {self.id}; Agent name: {self._agent.name}) started processing...")

        response = await self._agent.get_response(messages=message.body)  # type: ignore[arg-type]

        logger.debug(f"Sequential actor (Actor ID: {self.id}; Agent name: {self._agent.name}) finished processing.")

        await self._call_agent_response_callback(response.message)

        target_actor_id = await self.runtime.get(self._next_agent_type)
        await self.send_message(
            SequentialRequestMessage(body=response.message),
            target_actor_id,
            cancellation_token=ctx.cancellation_token,
        )


class CollectionActor(RoutedAgent):
    """A agent container for collection results from the last agent in the sequence."""

    def __init__(
        self,
        description: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]],
    ) -> None:
        """Initialize the collection actor."""
        self._result_callback = result_callback

        super().__init__(description=description)

    @message_handler
    async def _handle_message(self, message: SequentialRequestMessage, ctx: MessageContext) -> None:
        """Handle the last message."""
        await self._result_callback(message.body)


class SequentialOrchestration(OrchestrationBase[TIn, TOut]):
    """A sequential multi-agent pattern orchestration."""

    @override
    async def _start(
        self,
        task: DefaultTypeAlias,
        runtime: CoreRuntime,
        internal_topic_type: str,
        cancellation_token: CancellationToken,
    ) -> None:
        """Start the sequential pattern."""
        target_actor_id = await runtime.get(self._get_agent_actor_type(self._members[0], internal_topic_type))
        await runtime.send_message(
            SequentialRequestMessage(body=task),
            target_actor_id,
            cancellation_token=cancellation_token,
        )

    @override
    async def _prepare(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]],
    ) -> None:
        """Register the actors and orchestrations with the runtime and add the required subscriptions."""
        await self._register_members(runtime, internal_topic_type)
        await self._register_collection_actor(runtime, internal_topic_type, result_callback)

    async def _register_members(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
    ) -> None:
        """Register the members.

        The members will be registered in the reverse order so that the actor type of the next worker
        is available when the current worker is registered. This is important for the sequential
        orchestration, where actors need to know its next actor type to send the message to.

        Args:
            runtime (CoreRuntime): The agent runtime.
            internal_topic_type (str): The internal topic type for the orchestration that this actor is part of.

        Returns:
            str: The first actor type in the sequence.
        """
        next_actor_type = self._get_collection_actor_type(internal_topic_type)
        for index, agent in enumerate(reversed(self._members)):
            await SequentialAgentActor.register(
                runtime,
                self._get_agent_actor_type(agent, internal_topic_type),
                lambda agent=agent, next_actor_type=next_actor_type: SequentialAgentActor(  # type: ignore[misc]
                    agent,
                    internal_topic_type,
                    next_agent_type=next_actor_type,
                    agent_response_callback=self._agent_response_callback,
                ),
            )
            logger.debug(f"Registered agent actor of type {self._get_agent_actor_type(agent, internal_topic_type)}")
            next_actor_type = self._get_agent_actor_type(agent, internal_topic_type)

    async def _register_collection_actor(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]],
    ) -> None:
        """Register the collection actor."""
        await CollectionActor.register(
            runtime,
            self._get_collection_actor_type(internal_topic_type),
            lambda: CollectionActor(
                description="An internal agent that is responsible for collection results",
                result_callback=result_callback,
            ),
        )

    def _get_agent_actor_type(self, agent: Agent, internal_topic_type: str) -> str:
        """Get the actor type for an agent.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{agent.name}_{internal_topic_type}"

    def _get_collection_actor_type(self, internal_topic_type: str) -> str:
        """Get the collection actor type.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{CollectionActor.__name__}_{internal_topic_type}"
