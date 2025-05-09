# Copyright (c) Microsoft. All rights reserved.

from collections import defaultdict
from collections.abc import Awaitable, Callable, Sequence
from typing import DefaultDict

from semantic_kernel.agents.runtime.core.agent import Agent
from semantic_kernel.agents.runtime.core.agent_id import AgentId, CoreAgentId
from semantic_kernel.agents.runtime.core.agent_type import AgentType
from semantic_kernel.agents.runtime.core.subscription import Subscription
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
async def get_impl(
    *,
    id_or_type: AgentId | AgentType | str,
    key: str,
    lazy: bool,
    instance_getter: Callable[[AgentId], Awaitable[Agent]],
) -> AgentId:
    """Get the implementation of an agent."""
    if isinstance(id_or_type, AgentId):
        if not lazy:
            await instance_getter(id_or_type)

        return id_or_type

    type_str = id_or_type if isinstance(id_or_type, str) else id_or_type.type
    id = CoreAgentId(type_str, key)
    if not lazy:
        await instance_getter(id)

    return id


@experimental
class SubscriptionManager:
    """Manages subscriptions for agents."""

    def __init__(self) -> None:
        """Initialize the SubscriptionManager."""
        self._subscriptions: list[Subscription] = []
        self._seen_topics: set[TopicId] = set()
        self._subscribed_recipients: DefaultDict[TopicId, list[AgentId]] = defaultdict(list)

    @property
    def subscriptions(self) -> Sequence[Subscription]:
        """Get the list of subscriptions."""
        return self._subscriptions

    async def add_subscription(self, subscription: Subscription) -> None:
        """Add a subscription to the manager."""
        # Check if the subscription already exists
        if any(sub == subscription for sub in self._subscriptions):
            raise ValueError("Subscription already exists")

        self._subscriptions.append(subscription)
        self._rebuild_subscriptions(self._seen_topics)

    async def remove_subscription(self, id: str) -> None:
        """Remove a subscription from the manager."""
        # Check if the subscription exists
        if not any(sub.id == id for sub in self._subscriptions):
            raise ValueError("Subscription does not exist")

        def is_not_sub(x: Subscription) -> bool:
            return x.id != id

        self._subscriptions = list(filter(is_not_sub, self._subscriptions))

        # Rebuild the subscriptions
        self._rebuild_subscriptions(self._seen_topics)

    async def get_subscribed_recipients(self, topic: TopicId) -> list[AgentId]:
        """Get the list of recipients subscribed to a topic."""
        if topic not in self._seen_topics:
            self._build_for_new_topic(topic)
        return self._subscribed_recipients[topic]

    # TODO(evmattso): optimize this...
    def _rebuild_subscriptions(self, topics: set[TopicId]) -> None:
        """Rebuild the subscriptions for the given topics."""
        self._subscribed_recipients.clear()
        for topic in topics:
            self._build_for_new_topic(topic)

    def _build_for_new_topic(self, topic: TopicId) -> None:
        """Build the subscriptions for a new topic."""
        self._seen_topics.add(topic)
        for subscription in self._subscriptions:
            if subscription.is_match(topic):
                self._subscribed_recipients[topic].append(subscription.map_to_agent(topic))
