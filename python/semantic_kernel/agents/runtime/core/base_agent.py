# Copyright (c) Microsoft. All rights reserved.

import inspect
import warnings
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, ClassVar, TypeVar, final

from typing_extensions import Self

from semantic_kernel.agents.runtime.core.agent import Agent
from semantic_kernel.agents.runtime.core.agent_id import AgentId
from semantic_kernel.agents.runtime.core.agent_metadata import AgentMetadata, CoreAgentMetadata
from semantic_kernel.agents.runtime.core.agent_type import AgentType, CoreAgentType
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.serialization import MessageSerializer, try_get_known_serializers_for_type
from semantic_kernel.agents.runtime.core.subscription import Subscription, UnboundSubscription
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.agents.runtime.in_process.agent_instantiation_context import AgentInstantiationContext
from semantic_kernel.agents.runtime.in_process.subscription_context import SubscriptionInstantiationContext
from semantic_kernel.agents.runtime.in_process.type_prefix_subscription import TypePrefixSubscription
from semantic_kernel.utils.feature_stage_decorator import experimental

T = TypeVar("T", bound=Agent)

BaseAgentType = TypeVar("BaseAgentType", bound="BaseAgent")


# Decorator for adding an unbound subscription to an agent
@experimental
def subscription_factory(subscription: UnboundSubscription) -> Callable[[type[BaseAgentType]], type[BaseAgentType]]:
    """Decorator for adding an unbound subscription to an agent."""

    def decorator(cls: type[BaseAgentType]) -> type[BaseAgentType]:
        cls.internal_unbound_subscriptions_list.append(subscription)
        return cls

    return decorator


@experimental
def handles(
    msg_type: type[Any], serializer: MessageSerializer[Any] | list[MessageSerializer[Any]] | None = None
) -> Callable[[type[BaseAgentType]], type[BaseAgentType]]:
    """Decorator for associating a message type and corresponding serializer(s) with a BaseAgent or its subclass."""

    def decorator(cls: type[BaseAgentType]) -> type[BaseAgentType]:
        if serializer is None:
            serializer_list = try_get_known_serializers_for_type(msg_type)
        else:
            serializer_list = [serializer] if not isinstance(serializer, Sequence) else list(serializer)

        if not serializer_list:
            raise ValueError(f"No serializers found for type {msg_type!r}. Please provide an explicit serializer.")

        cls.internal_extra_handles_types.append((msg_type, serializer_list))
        return cls

    return decorator


@experimental
class BaseAgent(ABC, Agent):
    """Base class for all agents."""

    internal_unbound_subscriptions_list: ClassVar[list[UnboundSubscription]] = []
    """:meta private:"""
    internal_extra_handles_types: ClassVar[list[tuple[type[Any], list[MessageSerializer[Any]]]]] = []
    """:meta private:"""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize the class."""
        super().__init_subclass__(**kwargs)
        # Automatically set class_variable in each subclass so that they are not shared between subclasses
        cls.internal_extra_handles_types = []
        cls.internal_unbound_subscriptions_list = []

    @classmethod
    def _handles_types(cls) -> list[tuple[type[Any], list[MessageSerializer[Any]]]]:
        return cls.internal_extra_handles_types

    @classmethod
    def _unbound_subscriptions(cls) -> list[UnboundSubscription]:
        return cls.internal_unbound_subscriptions_list

    @property
    def metadata(self) -> AgentMetadata:
        """Get the metadata for this agent."""
        assert self._id is not None  # nosec
        return CoreAgentMetadata(key=self._id.key, type=self._id.type, description=self._description)

    def __init__(self, description: str) -> None:
        """Initialize the agent."""
        try:
            runtime = AgentInstantiationContext.current_runtime()
            id = AgentInstantiationContext.current_agent_id()
        except LookupError as e:
            raise RuntimeError(
                "BaseAgent must be instantiated within the context of an AgentRuntime. It cannot be directly "
                "instantiated."
            ) from e

        self._runtime: CoreRuntime = runtime
        self._id: AgentId = id
        if not isinstance(description, str):
            raise ValueError("Agent description must be a string")
        self._description = description

    @property
    def type(self) -> str:
        """Get the type of the agent."""
        return self.id.type

    @property
    def id(self) -> AgentId:
        """Get the id of the agent."""
        return self._id

    @property
    def runtime(self) -> CoreRuntime:
        """Get the runtime of the agent."""
        return self._runtime

    @final
    async def on_message(self, message: Any, ctx: MessageContext) -> Any:
        """Handle a message sent to this agent."""
        return await self.on_message_impl(message, ctx)

    @abstractmethod
    async def on_message_impl(self, message: Any, ctx: MessageContext) -> Any:
        """Handle a message sent to this agent."""
        ...

    async def send_message(
        self,
        message: Any,
        recipient: AgentId,
        *,
        cancellation_token: CancellationToken | None = None,
        message_id: str | None = None,
    ) -> Any:
        """Send a message to another agent."""
        if cancellation_token is None:
            cancellation_token = CancellationToken()

        return await self._runtime.send_message(
            message,
            sender=self.id,
            recipient=recipient,
            cancellation_token=cancellation_token,
            message_id=message_id,
        )

    async def publish_message(
        self,
        message: Any,
        topic_id: TopicId,
        *,
        cancellation_token: CancellationToken | None = None,
    ) -> None:
        """Publish a message."""
        await self._runtime.publish_message(message, topic_id, sender=self.id, cancellation_token=cancellation_token)

    async def save_state(self) -> Mapping[str, Any]:
        """Save the state of the agent."""
        warnings.warn("save_state not implemented", stacklevel=2)
        return {}

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """Load the state of the agent."""
        warnings.warn("load_state not implemented", stacklevel=2)
        pass

    async def close(self) -> None:
        """Close the agent."""
        pass

    @classmethod
    async def register(
        cls,
        runtime: CoreRuntime,
        type: str,
        factory: Callable[[], Self | Awaitable[Self]],
        *,
        skip_class_subscriptions: bool = False,
        skip_direct_message_subscription: bool = False,
    ) -> AgentType:
        """Register the agent with the runtime."""
        agent_type = CoreAgentType(type)
        agent_type = await runtime.register_factory(type=agent_type, agent_factory=factory, expected_class=cls)  # type: ignore
        if not skip_class_subscriptions:
            with SubscriptionInstantiationContext.populate_context(agent_type):
                subscriptions: list[Subscription] = []
                for unbound_subscription in cls._unbound_subscriptions():
                    subscriptions_list_result = unbound_subscription()
                    if inspect.isawaitable(subscriptions_list_result):
                        subscriptions_list = await subscriptions_list_result
                    else:
                        subscriptions_list = subscriptions_list_result

                    subscriptions.extend(subscriptions_list)
            for subscription in subscriptions:
                await runtime.add_subscription(subscription)

        if not skip_direct_message_subscription:
            # Additionally adds a special prefix subscription for this agent to receive direct messages
            await runtime.add_subscription(
                TypePrefixSubscription(
                    # The prefix MUST include ":" to avoid collisions with other agents
                    topic_type_prefix=agent_type.type + ":",
                    agent_type=agent_type.type,
                )
            )

        # TODO(evmattso): deduplication
        for _message_type, serializer in cls._handles_types():
            runtime.add_message_serializer(serializer)

        return agent_type
