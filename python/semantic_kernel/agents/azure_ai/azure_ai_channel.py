# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from azure.ai.projects.aio import AIProjectClient

    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental
class AzureAIChannel(AgentChannel):
    """AzureAI Channel."""

    def __init__(self, client: "AIProjectClient", thread_id: str) -> None:
        """Initialize the AzureAI Channel.

        Args:
            client: The AzureAI Project client.
            thread_id: The thread ID for the channel.
        """
        self.client = client
        self.thread_id = thread_id

    @override
    async def receive(self, history: list["ChatMessageContent"]) -> None:
        """Receive the conversation messages.

        Args:
            history: The conversation messages.
        """
        for message in history:
            await AgentThreadActions.create_message(self.client, self.thread_id, message)

    @override
    async def invoke(self, agent: "Agent", **kwargs) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the agent.

        Args:
            agent: The agent to invoke.
            kwargs: The keyword arguments.

        Yields:
            tuple[bool, ChatMessageContent]: The conversation messages.
        """
        from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent

        if not isinstance(agent, AzureAIAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(AzureAIAgent)}.")

        async for is_visible, message in AgentThreadActions.invoke(
            agent=agent,
            thread_id=self.thread_id,
            arguments=agent.arguments,
            kernel=agent.kernel,
            **kwargs,
        ):
            yield is_visible, message

    @override
    async def invoke_stream(
        self,
        agent: "Agent",
        messages: list["ChatMessageContent"],
        **kwargs,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent stream.

        Args:
            agent: The agent to invoke.
            messages: The conversation messages.
            kwargs: The keyword arguments.

        Yields:
            tuple[bool, StreamingChatMessageContent]: The conversation messages.
        """
        from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent

        if not isinstance(agent, AzureAIAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(AzureAIAgent)}.")

        async for message in AgentThreadActions.invoke_stream(
            agent=agent,
            thread_id=self.thread_id,
            output_messages=messages,
            arguments=agent.arguments,
            kernel=agent.kernel,
            **kwargs,
        ):
            yield message

    @override
    async def get_history(self) -> AsyncIterable["ChatMessageContent"]:
        """Get the conversation history.

        Yields:
            ChatMessageContent: The conversation history.
        """
        async for message in AgentThreadActions.get_messages(self.client, thread_id=self.thread_id):
            yield message

    @override
    async def reset(self) -> None:
        """Reset the agent's thread."""
        try:
            await self.client.agents.threads.delete(thread_id=self.thread_id)
        except Exception as e:
            raise AgentChatException(f"Failed to delete thread: {e}")
