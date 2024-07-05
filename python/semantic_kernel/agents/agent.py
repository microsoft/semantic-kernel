# Copyright (c) Microsoft. All rights reserved.

import uuid
from abc import ABC, abstractmethod

from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class Agent(ABC, KernelBaseModel):
    id: str
    description: str | None = None
    name: str | None = None

    def __init__(self, name: str | None = None, description: str | None = None, id: str | None = None):
        """Initialize the Agent."""
        if id is None:
            id = str(uuid.uuid4())
        super().__init__(id=id, description=description, name=name)

    @abstractmethod
    def get_channel_keys(self) -> list[str]:
        """Get the channel keys."""
        ...

    @abstractmethod
    async def create_channel(self) -> AgentChannel:
        """Create a channel."""
        ...
