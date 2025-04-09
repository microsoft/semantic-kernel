import sys
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent

from copilot_studio.copilot_agent_thread import CopilotAgentThread

class CopilotStudioAgentChannel(AgentChannel, ChatHistory):
    """A channel for interacting with Copilot Studio Agent."""

    thread: "CopilotAgentThread"

    @override
    async def receive(self, history: list[ChatMessageContent]) -> None:
        """Receive the conversation messages.

        Args:
            history: The history of messages in the conversation.
        """
        for incoming_message in history:
            self.messages.append(incoming_message)

    @override
    async def invoke(
        self,
        agent: "Agent",
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of ChatMessageContent with a boolean indicating if the
            message should be visible external to the agent.
        """
        from agents.copilot_studio.base.copilot_agent import CopilotAgent

        if not isinstance(agent, CopilotAgent):
            raise ValueError("Agent must be an instance of CopilotAgent.")
        if not self.messages:
            # This is not supposed to happen, as the channel won't get invoked
            # before it has received messages. This is just extra safety.
            raise AgentChatException("No chat history available.")

        try:
            # Pass thread object instead of just the ID
            async for response in agent.invoke(
                messages=self.messages[-1],
                thread=self.thread,
                **kwargs,
            ):
                # Append the response to the chat history
                self.messages.append(response)
                yield True, response
        except Exception as e:
            raise AgentInvokeException(f"Error invoking Copilot Studio agent: {e}")

    @override
    async def invoke_stream(
        self,
        agent: "Agent",
        messages: list[ChatMessageContent],
        **kwargs: Any,
    ) -> AsyncIterable[StreamingChatMessageContent]:
        """Perform a streaming interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            messages: The history of messages in the conversation.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of StreamingChatMessageContent.
        """
        # For now, just implement a placeholder that raises NotImplementedError
        raise NotImplementedError("Streaming is not supported by CopilotStudioAgentChannel yet")

    @override
    async def get_history(self) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the message history specific to this channel.

        Returns:
            An async iterable of ChatMessageContent.
        """
        for message in reversed(self.messages):
            yield message

    async def reset(self) -> None:
        """Reset the channel state."""
        self.messages.clear()