# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
import uuid
from collections.abc import AsyncIterable, Callable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from autogen import ConversableAgent

from semantic_kernel.agents.agent import Agent, AgentResponseItem, AgentThread
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException, AgentThreadOperationException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.agent_diagnostics.decorators import (
    trace_agent_get_response,
    trace_agent_invocation,
)

if TYPE_CHECKING:
    from autogen.cache import AbstractCache

    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AutoGenConversableAgentThread(AgentThread):
    """Azure AI Agent Thread class."""

    def __init__(self, chat_history: ChatHistory | None = None, thread_id: str | None = None) -> None:
        """Initialize the AutoGenConversableAgentThread Thread.

        Args:
            chat_history: The chat history for the thread. If None, a new ChatHistory instance will be created.
            thread_id: The ID of the thread. If None, a new thread will be created.
        """
        super().__init__()
        self._chat_history = chat_history or ChatHistory()
        self._id = thread_id

    @override
    async def _create(self) -> str:
        """Starts the thread and returns its ID."""
        if not self._id:
            self._id = f"thread_{uuid.uuid4().hex}"

        return self._id

    @override
    async def _delete(self) -> None:
        """Ends the current thread."""
        self._chat_history.clear()

    @override
    async def _on_new_message(self, new_message: str | ChatMessageContent) -> None:
        """Called when a new message has been contributed to the chat."""
        if isinstance(new_message, str):
            new_message = ChatMessageContent(role=AuthorRole.USER, content=new_message)

        if (
            not new_message.metadata
            or "thread_id" not in new_message.metadata
            or new_message.metadata["thread_id"] != self._id
        ):
            self._chat_history.add_message(new_message)

    async def get_messages(self) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the current chat history.

        Returns:
            An async iterable of ChatMessageContent.
        """
        if self._is_deleted:
            raise AgentThreadOperationException("Cannot retrieve chat history, since the thread has been deleted.")
        if self._id is None:
            await self.create()
        for message in self._chat_history.messages:
            yield message

    async def reduce(self) -> ChatHistory | None:
        """Reduce the chat history to a smaller size."""
        if self._id is None:
            raise AgentThreadOperationException("Cannot reduce chat history, since the thread is not currently active.")
        if not isinstance(self._chat_history, ChatHistoryReducer):
            return None
        return await self._chat_history.reduce()


@experimental
class AutoGenConversableAgent(Agent):
    """A Semantic Kernel wrapper around an AutoGen 0.2 `ConversableAgent`.

    This allows one to use it as a Semantic Kernel `Agent`. Note: this agent abstraction
    does not currently allow for the use of AgentGroupChat within Semantic Kernel.
    """

    conversable_agent: ConversableAgent

    def __init__(self, conversable_agent: ConversableAgent, **kwargs: Any) -> None:
        """Initialize the AutoGenConversableAgent.

        Args:
            conversable_agent: The existing AutoGen 0.2 ConversableAgent instance
            kwargs: Other Agent base class arguments (e.g. name, id, instructions)
        """
        args: dict[str, Any] = {
            "name": conversable_agent.name,
            "description": conversable_agent.description,
            "instructions": conversable_agent.system_message,
            "conversable_agent": conversable_agent,
        }

        if kwargs:
            args.update(kwargs)

        super().__init__(**args)

    @trace_agent_get_response
    @override
    async def get_response(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        """Get a response from the agent.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the conversation. If None, a new thread will be created.
            kwargs: Additional keyword arguments

        Returns:
            An AgentResponseItem of type ChatMessageContent object with the response and the thread.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: AutoGenConversableAgentThread(),
            expected_type=AutoGenConversableAgentThread,
        )
        assert thread.id is not None  # nosec

        reply = await self.conversable_agent.a_generate_reply(
            messages=[message.to_dict() async for message in thread.get_messages()],
            **kwargs,
        )

        logger.info("Called AutoGenConversableAgent.a_generate_reply.")

        return await self._create_reply_content(reply, thread)

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        recipient: "AutoGenConversableAgent | None" = None,
        clear_history: bool = True,
        silent: bool = True,
        cache: "AbstractCache | None" = None,
        max_turns: int | None = None,
        summary_method: str | Callable | None = ConversableAgent.DEFAULT_SUMMARY_METHOD,
        summary_args: dict | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem[ChatMessageContent]]:
        """A direct `invoke` method for the ConversableAgent.

        Args:
            messages: The input chat message content either as a string, ChatMessageContent or
                a list of strings or ChatMessageContent.
            thread: The thread to use for the conversation. If None, a new thread will be created.
            recipient: The recipient ConversableAgent to chat with
            clear_history: Whether to clear the chat history before starting. True by default.
            silent: Whether to suppress console output. True by default.
            cache: The cache to use for storing chat history
            max_turns: The maximum number of turns to chat for
            summary_method: The method to use for summarizing the chat
            summary_args: The arguments to pass to the summary method
            message: The initial message to send. If message is not provided,
                the agent will wait for the user to provide the first message.
            kwargs: Additional keyword arguments

        Yields:
            An AgentResponseItem of type ChatMessageContent object with the response and the thread.
        """
        thread = await self._ensure_thread_exists_with_messages(
            messages=messages,
            thread=thread,
            construct_thread=lambda: AutoGenConversableAgentThread(),
            expected_type=AutoGenConversableAgentThread,
        )
        assert thread.id is not None  # nosec

        if summary_args is None:
            summary_args = {}

        if recipient is not None:
            if not isinstance(recipient, AutoGenConversableAgent):
                raise AgentInvokeException(
                    f"Invalid recipient type: {type(recipient)}. "
                    "Recipient must be an instance of AutoGenConversableAgent."
                )

            messages = [message async for message in thread.get_messages()]
            chat_result = await self.conversable_agent.a_initiate_chat(
                recipient=recipient.conversable_agent,
                clear_history=clear_history,
                silent=silent,
                cache=cache,
                max_turns=max_turns,
                summary_method=summary_method,
                summary_args=summary_args,
                message=messages[-1].content,  # type: ignore
                **kwargs,
            )

            logger.info(f"Called AutoGenConversableAgent.a_initiate_chat with recipient: {recipient}.")

            for message in chat_result.chat_history:
                msg = AutoGenConversableAgent._to_chat_message_content(message)  # type: ignore
                await thread.on_new_message(msg)
                yield AgentResponseItem(
                    message=msg,
                    thread=thread,
                )
        else:
            reply = await self.conversable_agent.a_generate_reply(
                messages=[message.to_dict() async for message in thread.get_messages()],
            )

            logger.info("Called AutoGenConversableAgent.a_generate_reply.")

            yield await self._create_reply_content(reply, thread)

    @override
    def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        kernel: "Kernel | None" = None,
        arguments: KernelArguments | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseItem["StreamingChatMessageContent"]]:
        """Invoke the agent with a stream of messages."""
        raise NotImplementedError("The AutoGenConversableAgent does not support streaming.")

    @staticmethod
    def _to_chat_message_content(message: dict[str, Any]) -> ChatMessageContent:
        """Translate an AutoGen message to a Semantic Kernel ChatMessageContent."""
        items: list[TextContent | FunctionCallContent | FunctionResultContent] = []
        role = AuthorRole(message.get("role"))
        name: str = message.get("name", "")

        content = message.get("content")
        if content is not None:
            text = TextContent(text=content)
            items.append(text)

        if role == AuthorRole.ASSISTANT:
            tool_calls = message.get("tool_calls")
            if tool_calls is not None:
                for tool_call in tool_calls:
                    items.append(
                        FunctionCallContent(
                            id=tool_call.get("id"),
                            function_name=tool_call.get("name"),
                            arguments=tool_call.get("function").get("arguments"),
                        )
                    )

        if role == AuthorRole.TOOL:
            tool_responses = message.get("tool_responses")
            if tool_responses is not None:
                for tool_response in tool_responses:
                    items.append(
                        FunctionResultContent(
                            id=tool_response.get("tool_call_id"),
                            result=tool_response.get("content"),
                        )
                    )

        return ChatMessageContent(role=role, items=items, name=name)  # type: ignore

    async def _create_reply_content(
        self, reply: str | dict[str, Any], thread: AgentThread
    ) -> AgentResponseItem[ChatMessageContent]:
        response: ChatMessageContent
        if isinstance(reply, str):
            response = ChatMessageContent(content=reply, role=AuthorRole.ASSISTANT)
        elif isinstance(reply, dict):
            response = ChatMessageContent(**reply)
        else:
            raise AgentInvokeException(f"Unexpected reply type from `a_generate_reply`: {type(reply)}")

        await thread.on_new_message(response)

        return AgentResponseItem(
            message=response,
            thread=thread,
        )
