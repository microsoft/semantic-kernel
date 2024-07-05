# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING

from pydantic import BaseModel

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent


@experimental_class
class AgentChannel(ABC, BaseModel):
    @abstractmethod
    async def receive(
        self,
        history: list[ChatMessageContent],
    ) -> None:
        """Receive the conversation messages."""
        pass

    @abstractmethod
    async def invoke(
        self,
        agent: "Agent",
    ) -> AsyncIterable[ChatMessageContent]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat."""
        pass

    @abstractmethod
    async def get_history(
        self,
    ) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the message history specific to this channel."""
        pass
