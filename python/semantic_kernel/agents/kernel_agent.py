# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents.agent_base import AgentBase
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelAgent(AgentBase):
    """Base class for agents utilizing Kernel plugins or services."""

    instructions: str | None = None

    def __init__(
        self,
        service_id: str,
        name: str | None = None,
        instructions: str | None = None,
        id: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize the KernelAgent.

        Args:
            service_id: The service id for the agent.
            name: The name of the agent.
            instructions: The instructions for the agent.
            id: The unique identifier for the agent.
            description: The description of the agent.
        """
        super().__init__(service_id=service_id, name=name, id=id, description=description)
        self.instructions = instructions
