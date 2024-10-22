# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental_class
class SelectionStrategy(KernelBaseModel, ABC):
    """Contract for an agent selection strategy."""

    @abstractmethod
    async def next(self, agents: list["Agent"], history: list["ChatMessageContent"]) -> "Agent":
        """Select the next agent to interact with.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The next agent to interact with.
        """
        ...
