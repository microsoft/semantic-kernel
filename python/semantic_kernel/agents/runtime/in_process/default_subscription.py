# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TypeVar, overload

from semantic_kernel.agents.runtime.core.agent_type import AgentType
from semantic_kernel.agents.runtime.core.base_agent import BaseAgent, subscription_factory
from semantic_kernel.agents.runtime.core.exceptions import CantHandleException
from semantic_kernel.agents.runtime.in_process.subscription_context import SubscriptionInstantiationContext
from semantic_kernel.agents.runtime.in_process.type_subscription import TypeSubscription
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class DefaultSubscription(TypeSubscription):
    """The default subscription is designed to be a default for applications that only need global scope for agents.

    This topic by default uses the "default" topic type and attempts to detect the agent type to use based on the
    instantiation context.

    Args:
        topic_type (str, optional): The topic type to subscribe to. Defaults to "default".
        agent_type (str, optional): The agent type to use for the subscription. Defaults to None, in which case it
            will attempt to detect the agent type based on the instantiation context.
    """

    def __init__(self, topic_type: str = "default", agent_type: str | AgentType | None = None):
        """Initialize the DefaultSubscription."""
        if agent_type is None:
            try:
                agent_type = SubscriptionInstantiationContext.agent_type().type
            except RuntimeError as e:
                raise CantHandleException(
                    "If agent_type is not specified DefaultSubscription must be created within the subscription "
                    "callback in AgentRuntime.register"
                ) from e

        super().__init__(topic_type, agent_type)


BaseAgentType = TypeVar("BaseAgentType", bound="BaseAgent")


@overload
def default_subscription() -> Callable[[type[BaseAgentType]], type[BaseAgentType]]: ...


@overload
def default_subscription(cls: type[BaseAgentType]) -> type[BaseAgentType]: ...


@experimental
def default_subscription(
    cls: type[BaseAgentType] | None = None,
) -> Callable[[type[BaseAgentType]], type[BaseAgentType]] | type[BaseAgentType]:
    """Create a default subscription."""
    if cls is None:
        return subscription_factory(lambda: [DefaultSubscription()])
    return subscription_factory(lambda: [DefaultSubscription()])(cls)


@experimental
def type_subscription(topic_type: str) -> Callable[[type[BaseAgentType]], type[BaseAgentType]]:
    """Create a type subscription for the given topic type."""
    return subscription_factory(lambda: [DefaultSubscription(topic_type=topic_type)])
