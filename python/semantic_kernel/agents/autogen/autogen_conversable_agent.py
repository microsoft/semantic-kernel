# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable, Callable, Iterable
from typing import TYPE_CHECKING, Any

from autogen import ConversableAgent

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
    from autogen.cache import AbstractCache

    from semantic_kernel.agents.channels.agent_channel import AgentChannel
    from semantic_kernel.kernel import Kernel


class AutoGenConversableAgent(Agent):
    """A wrapper around an AutoGen 0.2 `ConversableAgent`.

    This allows one to use it as a Semantic Kernel `Agent`.
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

    def get_channel_keys(self) -> Iterable[str]:
        """Distinguish from other channels and incorporate the agent's identity."""
        yield f"{AutoGenConversableAgent.__name__}"
        yield self.id
        yield self.name

    async def create_channel(self) -> "AgentChannel":
        """Create an AutoGenChannel that uses the wrapped conversable_agent."""
        raise NotImplementedError("AutoGenConversableAgent does not support create_channel.")

    async def invoke(
        self,
        *,
        recipient: "ConversableAgent | None" = None,
        clear_history: bool = True,
        silent: bool = True,
        cache: "AbstractCache | None" = None,
        max_turns: int | None = None,
        summary_method: str | Callable | None = ConversableAgent.DEFAULT_SUMMARY_METHOD,
        summary_args: dict | None = {},
        message: dict | str | Callable | None = None,
        kernel: "Kernel | None" = None,
        arguments: KernelArguments | None = None,
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
            kernel: The kernel to use for chat
            arguments: The arguments to pass to the kernel
            kwargs: Additional keyword arguments
        """
        if arguments is None:
            arguments = KernelArguments(**kwargs)
        else:
            arguments.update(kwargs)

        kernel = kernel or self.kernel
        arguments = self.merge_arguments(arguments)

        if recipient is not None:
            chat_result = await self.conversable_agent.a_initiate_chat(
                recipient=recipient,
                clear_history=clear_history,
                silent=silent,
                cache=cache,
                max_turns=max_turns,
                summary_method=summary_method,
                summary_args=summary_args,
                message=message,  # type: ignore
                kernel=kernel,
                arguments=arguments,
                **kwargs,
            )

            for message in chat_result.chat_history:
                yield self._translate_message(message)
        else:
            reply = await self.conversable_agent.a_generate_reply(
                messages=[{"role": "user", "content": message}],
            )

            if isinstance(reply, str):
                yield ChatMessageContent(content=reply, role=AuthorRole.ASSISTANT)
            elif isinstance(reply, dict):
                yield ChatMessageContent(**reply)
            else:
                raise ValueError(f"Unexpected reply type: {type(reply)}")

    async def invoke_stream(
        self,
        message: str,
        kernel: "Kernel | None" = None,
        arguments: KernelArguments | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """A direct `invoke_stream` method for streaming usage."""
        # TODO(evmattso): Implement this method? Is there streaming in AG 0.2?
        raise NotImplementedError("invoke_stream is not yet implemented for AutoGenConversableAgent.")

    def _translate_message(self, message: dict) -> ChatMessageContent:
        """Translate an AutoGen message to a Semantic Kernel ChatMessageContent."""
        items = []
        role = AuthorRole.ASSISTANT
        match message.get("role"):
            case "user":
                role = AuthorRole.USER
            case "assistant":
                role = AuthorRole.ASSISTANT
            case "tool":
                role = AuthorRole.TOOL

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

        return ChatMessageContent(role=role, items=items, name=name)
