# Copyright (c) Microsoft. All rights reserved.

import uuid

from semantic_kernel.agents.runtime.core.agent_id import AgentId, CoreAgentId
from semantic_kernel.agents.runtime.core.agent_type import AgentType
from semantic_kernel.agents.runtime.core.exceptions import CantHandleException
from semantic_kernel.agents.runtime.core.subscription import Subscription
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class TypePrefixSubscription(Subscription):
    """This subscription matches on topics based on a prefix of the type and maps to agents.

    It uses the source of the topic as the agent key. This subscription causes each source to have
    its own agent instance.

    Args:
        topic_type_prefix (str): Topic type prefix to match against
        agent_type (str): Agent type to handle this subscription
    """

    def __init__(self, topic_type_prefix: str, agent_type: str | AgentType, id: str | None = None):
        """Initialize the TypePrefixSubscription."""
        self._topic_type_prefix = topic_type_prefix
        if isinstance(agent_type, AgentType):
            self._agent_type = agent_type.type
        else:
            self._agent_type = agent_type
        self._id = id or str(uuid.uuid4())

    @property
    def id(self) -> str:
        """Get the id of the subscription."""
        return self._id

    @property
    def topic_type_prefix(self) -> str:
        """Get the topic type prefix of the subscription."""
        return self._topic_type_prefix

    @property
    def agent_type(self) -> str:
        """Get the agent type of the subscription."""
        return self._agent_type

    def is_match(self, topic_id: TopicId) -> bool:
        """Check if the topic_id matches the subscription."""
        return topic_id.type.startswith(self._topic_type_prefix)

    def map_to_agent(self, topic_id: TopicId) -> AgentId:
        """Map the topic_id to an agent_id."""
        if not self.is_match(topic_id):
            raise CantHandleException("TopicId does not match the subscription")

        return CoreAgentId(type=self._agent_type, key=topic_id.source)

    def __eq__(self, other: object) -> bool:
        """Check if two subscriptions are equal."""
        if not isinstance(other, TypePrefixSubscription):
            return False

        return self.id == other.id or (
            self.agent_type == other.agent_type and self.topic_type_prefix == other.topic_type_prefix
        )
