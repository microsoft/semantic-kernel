# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents.agent import Agent
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelAgent(Agent):
    instructions: str | None = None

    def __init__(
        self,
        name: str | None = None,
        instructions: str | None = None,
        id: str | None = None,
        description: str | None = None,
    ):
        """Initialize the KernelAgent."""
        super().__init__(name=name, id=id, description=description)
        self.instructions = instructions
