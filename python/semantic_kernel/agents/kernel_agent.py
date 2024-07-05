# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents.agent import Agent
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelAgent(Agent):
    """Base class for agents utilizing Kernel plugins or services."""

    instructions: str | None = None

    def __init__(
        self,
        name: str | None = None,
        instructions: str | None = None,
        id: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize the KernelAgent.

        Args:
            name: The name of the agent.
            instructions: The instructions for the agent.
            id: The unique identifier for the agent.
            description: The description of the agent.
        """
        super().__init__(name=name, id=id, description=description)
        self.instructions = instructions
