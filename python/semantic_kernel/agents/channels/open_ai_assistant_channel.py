# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai import AsyncOpenAI

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.open_ai.assistant_content_generation import create_chat_message, generate_message_content
from semantic_kernel.agents.open_ai.assistant_thread_actions import AssistantThreadActions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent


@experimental
class OpenAIAssistantChannel(AgentChannel):
    """OpenAI Assistant Channel."""

    def __init__(self, client: AsyncOpenAI, thread_id: str) -> None:
        """Initialize the OpenAI Assistant Channel."""
        self.client = client
        self.thread_id = thread_id

    @override
    async def receive(self, history: list["ChatMessageContent"]) -> None:
        """Receive the conversation messages.

        Args:
            history: The conversation messages.
        """
        for message in history:
            if any(isinstance(item, FunctionCallContent) for item in message.items):
                continue
            await create_chat_message(self.client, self.thread_id, message)

    @override
    async def invoke(self, agent: "Agent", **kwargs: Any) -> AsyncIterable[tuple[bool, "ChatMessageContent"]]:
        """Invoke the agent.

        Args:
            agent: The agent to invoke.
            kwargs: The keyword arguments.

        Yields:
            tuple[bool, ChatMessageContent]: The conversation messages.
        """
        from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent

        if not isinstance(agent, OpenAIAssistantAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(OpenAIAssistantAgent)}.")

        async for is_visible, message in AssistantThreadActions.invoke(agent=agent, thread_id=self.thread_id, **kwargs):
            yield is_visible, message

    @override
    async def invoke_stream(
        self, agent: "Agent", messages: list[ChatMessageContent], **kwargs: Any
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent stream.

        Args:
            agent: The agent to invoke.
            messages: The conversation messages.
            kwargs: The keyword arguments.

        Yields:
            tuple[bool, StreamingChatMessageContent]: The conversation messages.
        """
        from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent

        if not isinstance(agent, OpenAIAssistantAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(OpenAIAssistantAgent)}.")

        async for message in AssistantThreadActions.invoke_stream(
            agent=agent, thread_id=self.thread_id, output_messages=messages, **kwargs
        ):
            yield message

    @override
    async def get_history(self) -> AsyncIterable["ChatMessageContent"]:
        """Get the conversation history.

        Yields:
            ChatMessageContent: The conversation history.
        """
        agent_names: dict[str, Any] = {}

        thread_messages = await self.client.beta.threads.messages.list(
            thread_id=self.thread_id, limit=100, order="desc"
        )
        for message in thread_messages.data:
            assistant_name = None
            if message.assistant_id and message.assistant_id not in agent_names:
                agent = await self.client.beta.assistants.retrieve(message.assistant_id)
                if agent.name:
                    agent_names[message.assistant_id] = agent.name
            assistant_name = agent_names.get(message.assistant_id) if message.assistant_id else message.assistant_id

            content: ChatMessageContent = generate_message_content(str(assistant_name), message)

            if len(content.items) > 0:
                yield content

    @override
    async def reset(self) -> None:
        """Reset the agent's thread."""
        try:
            await self.client.beta.threads.delete(thread_id=self.thread_id)
        except Exception as e:
            raise AgentChatException(f"Failed to delete thread: {e}")
