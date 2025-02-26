# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)


@experimental
class BedrockAgentChannel(AgentChannel, ChatHistory):
    """An AgentChannel for a BedrockAgent that is based on a ChatHistory.

    This channel allows Bedrock agents to interact with other types of agents in Semantic Kernel in an AgentGroupChat.
    However, since Bedrock agents require the chat history to alternate between user and agent messages, this channel
    will preprocess the chat history to ensure that it meets the requirements of the Bedrock agent. When an invalid
    pattern is detected, the channel will insert a placeholder user or assistant message to ensure that the chat history
    alternates between user and agent messages.
    """

    MESSAGE_PLACEHOLDER: ClassVar[str] = "[SILENCE]"

    @override
    async def invoke(self, agent: "Agent", **kwargs: Any) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of ChatMessageContent with a boolean indicating if the
            message should be visible external to the agent.
        """
        from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

        if not isinstance(agent, BedrockAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(BedrockAgent)}.")
        if not self.messages:
            # This is not supposed to happen, as the channel won't get invoked
            # before it has received messages. This is just extra safety.
            raise AgentChatException("No chat history available.")

        # Preprocess chat history
        self._ensure_history_alternates()
        self._ensure_last_message_is_user()

        session_id = BedrockAgent.create_session_id()
        async for message in agent.invoke(
            session_id,
            self.messages[-1].content,
            sessionState=self._parse_chat_history_to_session_state(),
        ):
            self.messages.append(message)
            # All messages from Bedrock agents are user facing, i.e., function calls are not returned as messages
            yield True, message

    @override
    async def invoke_stream(
        self,
        agent: "Agent",
        messages: list[ChatMessageContent],
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """Perform a streaming interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            messages: The history of messages in the conversation.
            kwargs: Additional keyword arguments.

        Returns:
            An async iterable of ChatMessageContent.
        """
        from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

        if not isinstance(agent, BedrockAgent):
            raise AgentChatException(f"Agent is not of the expected type {type(BedrockAgent)}.")
        if not self.messages:
            raise AgentChatException("No chat history available.")

        # Preprocess chat history
        self._ensure_history_alternates()
        self._ensure_last_message_is_user()

        session_id = BedrockAgent.create_session_id()
        full_message: list[StreamingChatMessageContent] = []
        async for message_chunk in agent.invoke_stream(
            session_id,
            self.messages[-1].content,
            sessionState=self._parse_chat_history_to_session_state(),
        ):
            yield message_chunk
            full_message.append(message_chunk)

        messages.append(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content="".join([message.content for message in full_message]),
                name=agent.name,
                inner_content=full_message,
                ai_model_id=agent.agent_model.foundation_model,
            )
        )

    @override
    async def receive(
        self,
        history: list[ChatMessageContent],
    ) -> None:
        """Receive the conversation messages.

        Bedrock requires the chat history to alternate between user and agent messages.
        Thus, when receiving the history, the message sequence will be mutated by inserting
        empty agent or user messages as needed.

        Args:
            history: The history of messages in the conversation.
        """
        for incoming_message in history:
            if not self.messages or self.messages[-1].role != incoming_message.role:
                self.messages.append(incoming_message)
            else:
                self.messages.append(
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT if incoming_message.role == AuthorRole.USER else AuthorRole.USER,
                        content=self.MESSAGE_PLACEHOLDER,
                    )
                )
                self.messages.append(incoming_message)

    @override
    async def get_history(  # type: ignore
        self,
    ) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the message history specific to this channel.

        Returns:
            An async iterable of ChatMessageContent.
        """
        for message in reversed(self.messages):
            yield message

    @override
    async def reset(self) -> None:
        """Reset the channel state."""
        self.messages.clear()

    # region chat history preprocessing and parsing

    def _ensure_history_alternates(self):
        """Ensure that the chat history alternates between user and agent messages."""
        if not self.messages or len(self.messages) == 1:
            return

        current_index = 1
        while current_index < len(self.messages):
            if self.messages[current_index].role == self.messages[current_index - 1].role:
                self.messages.insert(
                    current_index,
                    ChatMessageContent(
                        role=AuthorRole.ASSISTANT
                        if self.messages[current_index].role == AuthorRole.USER
                        else AuthorRole.USER,
                        content=self.MESSAGE_PLACEHOLDER,
                    ),
                )
                current_index += 2
            else:
                current_index += 1

    def _ensure_last_message_is_user(self):
        """Ensure that the last message in the chat history is a user message."""
        if self.messages and self.messages[-1].role == AuthorRole.ASSISTANT:
            self.messages.append(
                ChatMessageContent(
                    role=AuthorRole.USER,
                    content=self.MESSAGE_PLACEHOLDER,
                )
            )

    def _parse_chat_history_to_session_state(self) -> dict[str, Any]:
        """Parse the chat history to a session state."""
        session_state: dict[str, Any] = {"conversationHistory": {"messages": []}}
        if len(self.messages) > 1:
            # We don't take the last message as it needs to be sent separately in another parameter
            for message in self.messages[:-1]:
                if message.role not in [AuthorRole.USER, AuthorRole.ASSISTANT]:
                    logger.debug(f"Skipping message with unsupported role: {message}")
                    continue
                session_state["conversationHistory"]["messages"].append({
                    "content": [{"text": message.content}],
                    "role": message.role.value,
                })

        return session_state

    # endregion
