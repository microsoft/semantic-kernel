import logging
from typing import TYPE_CHECKING, Any, AsyncIterable, Iterable

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException

if TYPE_CHECKING:
    from autogen import ConversableAgent

logger: logging.Logger = logging.getLogger(__name__)


class AutoGenChannel(AgentChannel):
    """Minimal bridging channel between a Semantic Kernel conversation and an AutoGen ConversableAgent.

    We store conversation messages in memory
    and pass them to the underlying ConversableAgent as needed.
    """

    def __init__(self, conversable_agent: "ConversableAgent") -> None:
        """Create an AutoGenChannel with a reference to the user's `ConversableAgent`."""
        self._conversable_agent = conversable_agent
        # We keep an internal buffer of ChatMessageContent as SK sees them
        self._history: list[ChatMessageContent] = []

    async def receive(self, history: list[ChatMessageContent]) -> None:
        """Called by AgentChat to deliver conversation messages.

        We append them to our local buffer and use them for context.
        """
        self._history.extend(history)

    def invoke(
        self,
        agent: "Agent",
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Perform a discrete single-step interaction using the AutoGen `ConversableAgent`.

        For a minimal bridging, we:
        1. Take the last user message from our local `_history`.
        2. Ask the AutoGen agent to generate a reply.
        3. Yield one ChatMessageContent with role=ASSISTANT.

        Returns an async generator yielding `(bool, ChatMessageContent)`.
        The boolean indicates if the message should be visible externally.
        """
        return self._invoke_impl()

    async def _invoke_impl(self) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        if not self._history:
            raise AgentChatException("No messages in history to prompt the AutoGenConversableAgent.")

        # The last message from the user:
        last_message = self._history[-1]

        if last_message.role != AuthorRole.USER:
            logger.warning(
                "Warning: The last message in the conversation isn't from the user. "
                "AutoGen generally expects the final message to be user input."
            )

        user_text = last_message.content

        # Here we call the underlying AutoGen ConversableAgent in a blocking way
        # or if your `generate_reply` is synchronous, you can do run_in_executor, etc.
        # For simplicity, let's assume generate_reply is synchronous:
        reply_text = self._conversable_agent.generate_reply(messages=[{"role": "user", "content": user_text}])

        # Produce a ChatMessageContent with an assistant role
        content = ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            content=reply_text,
        )

        # We append it to local history so the channel has the full conversation
        self._history.append(content)

        # Return it to the SK pipeline
        yield True, content

    def invoke_stream(
        self,
        agent: "Agent",
        messages: list["ChatMessageContent"],
        **kwargs,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Perform a single-step streaming interaction. If your `ConversableAgent`
        does not natively support streaming, we simply yield one chunk.
        """
        return self._invoke_stream_impl(messages)

    async def _invoke_stream_impl(self, messages: list[ChatMessageContent]) -> AsyncIterable[ChatMessageContent]:
        # Add the incoming messages to local history
        await self.receive(messages)

        # For streaming, we will just yield once if no true streaming is available.
        # If your ConversableAgent has partial streaming chunks, you would yield incrementally.
        last_message = self._history[-1]
        user_text = last_message.content

        reply_text = self._conversable_agent.generate_reply(messages=[{"role": "user", "content": user_text}])
        content = ChatMessageContent(role=AuthorRole.ASSISTANT, content=reply_text)
        self._history.append(content)

        # Return as a single chunk
        yield content

    async def get_history(self) -> AsyncIterable["ChatMessageContent"]:
        """Return the conversation messages so far in reverse (latest first)."""
        for message in reversed(self._history):
            yield message

    async def reset(self) -> None:
        """Clear the local conversation buffer."""
        self._history.clear()


class AutoGenAgent(Agent):
    """A slim wrapper around an AutoGen 0.2 `ConversableAgent`, letting you use it as
    a Semantic Kernel `Agent`. You can pass in your existing ConversableAgent to the
    constructor, and then rely on SK's `invoke` or `invoke_stream` pattern.
    """

    def __init__(self, conversable_agent: "ConversableAgent", **kwargs: Any) -> None:
        """Initialize the AutoGenAgent.

        :param conversable_agent: The existing AutoGen 0.2 ConversableAgent instance
        :param kwargs: Other Agent base class arguments (e.g. name, id, instructions)
        """
        super().__init__(**kwargs)
        self._conversable_agent = conversable_agent

    def get_channel_keys(self) -> Iterable[str]:
        """Distinguish from other channels and incorporate the agent's identity."""
        yield "AutoGenAgent"
        yield self.id
        yield self.name

    async def create_channel(self) -> AgentChannel:
        """Create an AutoGenChannel that uses the wrapped conversable_agent."""
        return AutoGenChannel(self._conversable_agent)
