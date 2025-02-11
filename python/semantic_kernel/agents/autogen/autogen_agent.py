# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable, Iterable
from typing import TYPE_CHECKING, Any, Callable

from autogen import ConversableAgent

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
    from autogen.cache import AbstractCache

    from semantic_kernel.agents.channels.agent_channel import AgentChannel
    from semantic_kernel.kernel import Kernel


class AutoGenAgent(Agent):
    """A slim wrapper around an AutoGen 0.2 `ConversableAgent`.

    This allows one to use it as a Semantic Kernel `Agent`. Pass in your existing
    ConversableAgent to the constructor, and then rely on SK's `invoke` or `invoke_stream` pattern.
    """

    conversable_agent: ConversableAgent

    def __init__(self, conversable_agent: ConversableAgent, **kwargs: Any) -> None:
        """Initialize the AutoGenAgent.

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
        yield f"{AutoGenAgent.__name__}"
        yield self.id
        yield self.name

    async def create_channel(self) -> "AgentChannel":
        """Create an AutoGenChannel that uses the wrapped conversable_agent."""
        raise NotImplementedError("AutoGenAgent does not support create_channel.")

    async def invoke(
        self,
        *,
        recipient: "ConversableAgent | None" = None,
        clear_history: bool = True,
        silent: bool | None = None,
        cache: "AbstractCache | None" = None,
        max_turns: int | None = None,
        summary_method: str | Callable | None = ConversableAgent.DEFAULT_SUMMARY_METHOD,
        summary_args: dict | None = {},
        message: dict | str | Callable | None = None,
        kernel: "Kernel | None" = None,
        arguments: KernelArguments | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        """A direct `invoke` method, similar to AzureAIAgent, for convenience.

        Typically, in the SK environment, `AgentChat` calls create_channel, then calls channel.invoke.
        But you can also allow the user to call `invoke` directly for a simpler usage pattern.
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
                message=message,
                kernel=kernel,
                arguments=arguments,
                **kwargs,
            )

            for message in chat_result.chat_history:
                yield ChatMessageContent(**message)
        else:
            reply = await self.conversable_agent.a_generate_reply(
                messages=[{"role": "user", "content": message}],
            )

            if isinstance(reply, str):
                yield ChatMessageContent(content=reply, role="assistant")
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
        # TODO(evmattso): Implement this method.
        raise NotImplementedError("invoke_stream is not yet implemented for AutoGenAgent.")
