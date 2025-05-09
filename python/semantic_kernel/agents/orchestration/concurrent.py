# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from collections.abc import Awaitable, Callable

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.orchestration.agent_actor_base import AgentActorBase
from semantic_kernel.agents.orchestration.orchestration_base import (
    ChatMessageContent,
    DefaultTypeAlias,
    OrchestrationBase,
    TIn,
    TOut,
)
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import RoutedAgent, message_handler
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.agents.runtime.in_process.type_subscription import TypeSubscription
from semantic_kernel.kernel_pydantic import KernelBaseModel

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


logger: logging.Logger = logging.getLogger(__name__)


class ConcurrentRequestMessage(KernelBaseModel):
    """A request message type for concurrent agents."""

    body: DefaultTypeAlias


class ConcurrentResponseMessage(KernelBaseModel):
    """A response message type for concurrent agents."""

    body: ChatMessageContent


class ConcurrentAgentActor(AgentActorBase):
    """A agent actor for concurrent agents that process tasks."""

    def __init__(
        self,
        agent: Agent,
        internal_topic_type: str,
        collection_agent_type: str,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
    ) -> None:
        """Initialize the agent actor."""
        self._collection_agent_type = collection_agent_type
        super().__init__(
            agent=agent,
            internal_topic_type=internal_topic_type,
            agent_response_callback=agent_response_callback,
        )

    @message_handler
    async def _handle_message(self, message: ConcurrentRequestMessage, ctx: MessageContext) -> None:
        """Handle a message."""
        logger.debug(f"Concurrent actor (Actor ID: {self.id}; Agent name: {self._agent.name}) started processing...")

        response = await self._agent.get_response(
            messages=message.body,  # type: ignore[arg-type]
        )

        logger.debug(f"Concurrent actor (Actor ID: {self.id}; Agent name: {self._agent.name}) finished processing.")

        await self._call_agent_response_callback(response.message)

        target_actor_id = await self.runtime.get(self._collection_agent_type)
        await self.send_message(
            ConcurrentResponseMessage(body=response.message),
            target_actor_id,
            cancellation_token=ctx.cancellation_token,
        )


class CollectionActor(RoutedAgent):
    """A agent container for collecting results from concurrent agents."""

    def __init__(
        self,
        description: str,
        expected_answer_count: int,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the collection agent container."""
        self._expected_answer_count = expected_answer_count
        self._result_callback = result_callback
        self._results: list[ChatMessageContent] = []
        self._lock = asyncio.Lock()

        super().__init__(description=description)

    @message_handler
    async def _handle_message(self, message: ConcurrentResponseMessage, ctx: MessageContext) -> None:
        async with self._lock:
            self._results.append(message.body)

        if len(self._results) == self._expected_answer_count:
            logger.debug(f"Collection actor (Actor ID: {self.id}) finished processing all responses.")
            if self._result_callback:
                await self._result_callback(self._results)


class ConcurrentOrchestration(OrchestrationBase[TIn, TOut]):
    """A concurrent multi-agent pattern orchestration."""

    @override
    async def _start(
        self,
        task: DefaultTypeAlias,
        runtime: CoreRuntime,
        internal_topic_type: str,
        cancellation_token: CancellationToken,
    ) -> None:
        """Start the concurrent pattern."""
        await runtime.publish_message(
            ConcurrentRequestMessage(body=task),
            TopicId(internal_topic_type, self.__class__.__name__),
            cancellation_token=cancellation_token,
        )

    @override
    async def _prepare(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        """Register the actors and orchestrations with the runtime and add the required subscriptions."""
        await asyncio.gather(*[
            self._register_members(
                runtime,
                internal_topic_type,
            ),
            self._register_collection_actor(
                runtime,
                internal_topic_type,
                result_callback=result_callback,
            ),
            self._add_subscriptions(
                runtime,
                internal_topic_type,
            ),
        ])

    async def _register_members(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
    ) -> None:
        """Register the members."""

        async def _internal_helper(agent: Agent) -> None:
            await ConcurrentAgentActor.register(
                runtime,
                self._get_agent_actor_type(agent, internal_topic_type),
                lambda agent=agent: ConcurrentAgentActor(  # type: ignore[misc]
                    agent,
                    internal_topic_type,
                    collection_agent_type=self._get_collection_actor_type(internal_topic_type),
                    agent_response_callback=self._agent_response_callback,
                ),
            )

        await asyncio.gather(*[_internal_helper(agent) for agent in self._members])

    async def _register_collection_actor(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        await CollectionActor.register(
            runtime,
            self._get_collection_actor_type(internal_topic_type),
            lambda: CollectionActor(
                description="An internal agent that is responsible for collection results",
                expected_answer_count=len(self._members),
                result_callback=result_callback,
            ),
        )

    async def _add_subscriptions(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
    ) -> None:
        await asyncio.gather(*[
            runtime.add_subscription(
                TypeSubscription(
                    internal_topic_type,
                    self._get_agent_actor_type(agent, internal_topic_type),
                )
            )
            for agent in self._members
        ])

    def _get_agent_actor_type(self, worker: Agent, internal_topic_type: str) -> str:
        """Get the container type for an agent.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{worker.name}_{internal_topic_type}"

    def _get_collection_actor_type(self, internal_topic_type: str) -> str:
        """Get the collection agent type.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{CollectionActor.__name__}_{internal_topic_type}"
