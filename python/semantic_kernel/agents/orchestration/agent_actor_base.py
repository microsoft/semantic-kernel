# Copyright (c) Microsoft. All rights reserved.


import inspect
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from semantic_kernel.agents.agent import Agent, AgentThread
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import RoutedAgent
from semantic_kernel.contents import ChatHistory, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


@experimental
class ActorBase(RoutedAgent):
    """A base class for actors running in the AgentRuntime."""

    @override
    async def on_message_impl(self, message: Any, ctx: MessageContext) -> Any | None:
        """Handle a message.

        Stop the handling of the message if the cancellation token is cancelled.
        """
        if ctx.cancellation_token.is_cancelled():
            return None

        return await super().on_message_impl(message, ctx)


@experimental
class AgentActorBase(ActorBase):
    """A agent actor for multi-agent orchestration running on Agent runtime."""

    def __init__(
        self,
        agent: Agent,
        internal_topic_type: str,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
        streaming_agent_response_callback: Callable[[StreamingChatMessageContent, bool], Awaitable[None] | None]
        | None = None,
    ) -> None:
        """Initialize the agent container.

        Args:
            agent (Agent): An agent to be run in the container.
            internal_topic_type (str): The topic type of the internal topic.
            agent_response_callback (Callable | None): A function that is called when a full response is produced
                by the agents.
            streaming_agent_response_callback (Callable | None): A function that is called when a streaming response
                is produced by the agents.
        """
        self._agent = agent
        self._internal_topic_type = internal_topic_type
        self._agent_response_callback = agent_response_callback
        self._streaming_agent_response_callback = streaming_agent_response_callback

        self._agent_thread: AgentThread | None = None
        # Chat history to temporarily store messages before the agent thread is created
        self._chat_history = ChatHistory()

        ActorBase.__init__(self, description=agent.description or "Semantic Kernel Agent")

    async def _call_agent_response_callback(self, message: DefaultTypeAlias) -> None:
        """Call the agent_response_callback function if it is set.

        Args:
            message (DefaultTypeAlias): The message to be sent to the agent_response_callback.
        """
        if self._agent_response_callback:
            if inspect.iscoroutinefunction(self._agent_response_callback):
                await self._agent_response_callback(message)
            else:
                self._agent_response_callback(message)

    async def _call_streaming_agent_response_callback(
        self,
        message_chunk: StreamingChatMessageContent,
        is_final: bool,
    ) -> None:
        """Call the streaming_agent_response_callback function if it is set.

        Args:
            message_chunk (StreamingChatMessageContent): The message chunk.
            is_final (bool): Whether this is the final chunk of the response.
        """
        if self._streaming_agent_response_callback:
            if inspect.iscoroutinefunction(self._streaming_agent_response_callback):
                await self._streaming_agent_response_callback(message_chunk, is_final)
            else:
                self._streaming_agent_response_callback(message_chunk, is_final)

    async def _invoke_agent(self, additional_messages: DefaultTypeAlias | None = None, **kwargs) -> ChatMessageContent:
        """Invoke the agent with the current chat history or thread and optionally additional messages.

        Args:
            additional_messages (DefaultTypeAlias | None): Additional messages to be sent to the agent.
            **kwargs: Additional keyword arguments to be passed to the agent's invoke method:
                - kernel: The kernel to use for the agent invocation.

        Returns:
            DefaultTypeAlias: The response from the agent.
        """
        streaming_message_buffer: list[StreamingChatMessageContent] = []
        messages = self._create_messages(additional_messages)

        async for response_item in self._agent.invoke_stream(messages=messages, thread=self._agent_thread, **kwargs):  # type: ignore[arg-type]
            # Buffer message chunks and stream them with correct is_final flag.
            streaming_message_buffer.append(response_item.message)
            if len(streaming_message_buffer) > 1:
                await self._call_streaming_agent_response_callback(streaming_message_buffer[-2], is_final=False)
            if self._agent_thread is None:
                self._agent_thread = response_item.thread

        if streaming_message_buffer:
            # Call the callback for the last message chunk with is_final=True.
            await self._call_streaming_agent_response_callback(streaming_message_buffer[-1], is_final=True)

        if not streaming_message_buffer:
            raise RuntimeError(f'Agent "{self._agent.name}" did not return any response.')

        # Build the full response from the streaming messages
        full_response = sum(streaming_message_buffer[1:], streaming_message_buffer[0])
        await self._call_agent_response_callback(full_response)

        return full_response

    def _create_messages(self, additional_messages: DefaultTypeAlias | None = None) -> list[ChatMessageContent]:
        """Create a list of messages to be sent to the agent along with a potential thread.

        Args:
            additional_messages (DefaultTypeAlias | None): Additional messages to be sent to the agent.

        Returns:
            list[ChatMessageContent]: A list of messages to be sent to the agent.
        """
        base_messages = self._chat_history.messages[:] if self._agent_thread is None else []

        if additional_messages is None:
            return base_messages

        if isinstance(additional_messages, list):
            return base_messages + additional_messages
        return [*base_messages, additional_messages]
