# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncIterable, Callable
from typing import TYPE_CHECKING, Any

from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from autogen import ConversableAgent

from semantic_kernel.agents.agent import Agent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException
from semantic_kernel.functions.kernel_arguments import KernelArguments
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
    async def get_response(self, message: str) -> ChatMessageContent:
        """Get a response from the agent.

        Args:
            message: The message to send.

        Returns:
            A ChatMessageContent object with the response.
        """
        reply = await self.conversable_agent.a_generate_reply(
            messages=[{"role": "user", "content": message}],
        )

        logger.info("Called AutoGenConversableAgent.a_generate_reply.")

        if isinstance(reply, str):
            return ChatMessageContent(content=reply, role=AuthorRole.ASSISTANT)
        if isinstance(reply, dict):
            return ChatMessageContent(**reply)

        raise AgentInvokeException(f"Unexpected reply type from `a_generate_reply`: {type(reply)}")

    @trace_agent_invocation
    @override
    async def invoke(
        self,
        *,
        recipient: "AutoGenConversableAgent | None" = None,
        clear_history: bool = True,
        silent: bool = True,
        cache: "AbstractCache | None" = None,
        max_turns: int | None = None,
        summary_method: str | Callable | None = ConversableAgent.DEFAULT_SUMMARY_METHOD,
        summary_args: dict | None = {},
        message: dict | str | Callable | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """A direct `invoke` method for the ConversableAgent.

        Args:
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
        """
        if recipient is not None:
            if not isinstance(recipient, AutoGenConversableAgent):
                raise AgentInvokeException(
                    f"Invalid recipient type: {type(recipient)}. "
                    "Recipient must be an instance of AutoGenConversableAgent."
                )

            chat_result = await self.conversable_agent.a_initiate_chat(
                recipient=recipient.conversable_agent,
                clear_history=clear_history,
                silent=silent,
                cache=cache,
                max_turns=max_turns,
                summary_method=summary_method,
                summary_args=summary_args,
                message=message,  # type: ignore
                **kwargs,
            )

            logger.info(f"Called AutoGenConversableAgent.a_initiate_chat with recipient: {recipient}.")

            for message in chat_result.chat_history:
                yield AutoGenConversableAgent._to_chat_message_content(message)  # type: ignore
        else:
            reply = await self.conversable_agent.a_generate_reply(
                messages=[{"role": "user", "content": message}],
            )

            logger.info("Called AutoGenConversableAgent.a_generate_reply.")

            if isinstance(reply, str):
                yield ChatMessageContent(content=reply, role=AuthorRole.ASSISTANT)
            elif isinstance(reply, dict):
                yield ChatMessageContent(**reply)
            else:
                raise AgentInvokeException(f"Unexpected reply type from `a_generate_reply`: {type(reply)}")

    @override
    def invoke_stream(
        self,
        message: str,
        kernel: "Kernel | None" = None,
        arguments: KernelArguments | None = None,
        **kwargs: Any,
    ) -> AsyncIterable["StreamingChatMessageContent"]:
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
