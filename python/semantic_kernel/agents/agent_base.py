# Copyright (c) Microsoft. All rights reserved.

import uuid
from abc import ABC, abstractmethod

from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AgentBase(ABC, KernelBaseModel):
    """Base abstraction for all Semantic Kernel agents.

    An agent instance may participate in one or more conversations.
    A conversation may include one or more agents.
    In addition to identity and descriptive meta-data, an Agent
    must define its communication protocol, or AgentChannel.
    """

    service_id: str
    id: str
    description: str | None = None
    name: str | None = None

    def __init__(self, service_id: str, name: str | None = None, description: str | None = None, id: str | None = None):
        """Initialize the Agent.

        Args:
            service_id: The unique identifier of the service.
            name: The name of the agent (optional).
            description: The description of the agent (optional).
            id: The unique identifier of the agent (optional). If no id is provided,
                a new UUID will be generated.
        """
        if id is None:
            id = str(uuid.uuid4())
        super().__init__(service_id=service_id, id=id, description=description, name=name)

    @abstractmethod
    def get_channel_keys(self) -> list[str]:
        """Get the channel keys.

        Returns:
            A list of channel keys.
        """
        ...

    @abstractmethod
    async def create_channel(self) -> AgentChannel:
        """Create a channel.

        Returns:
            An instance of AgentChannel.
        """
        ...
