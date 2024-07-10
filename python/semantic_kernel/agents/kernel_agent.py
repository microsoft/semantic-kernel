# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents.agent_base import AgentBase
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelAgent(AgentBase):
    """Base class for agents utilizing Kernel plugins or services.

    Attributes:
        instructions: The instructions for the agent.
    """

    instructions: str | None = None
