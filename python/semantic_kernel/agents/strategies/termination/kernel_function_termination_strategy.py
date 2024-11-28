# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from inspect import isawaitable
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class KernelFunctionTerminationStrategy(TerminationStrategy):
    """A termination strategy that uses a kernel function to determine termination."""

    DEFAULT_AGENT_VARIABLE_NAME: ClassVar[str] = "_agent_"
    DEFAULT_HISTORY_VARIABLE_NAME: ClassVar[str] = "_history_"

    agent_variable_name: str | None = Field(default=DEFAULT_AGENT_VARIABLE_NAME)
    history_variable_name: str | None = Field(default=DEFAULT_HISTORY_VARIABLE_NAME)
    arguments: KernelArguments | None = None
    function: KernelFunction
    kernel: Kernel
    result_parser: Callable[..., bool] = Field(default_factory=lambda: (lambda: True))

    async def should_agent_terminate(
        self,
        agent: "Agent",
        history: list[ChatMessageContent],
    ) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.

        Returns:
            True if the agent should terminate, False otherwise
        """
        original_arguments = self.arguments or KernelArguments()
        execution_settings = original_arguments.execution_settings or {}

        messages = [message.to_dict(role_key="role", content_key="content") for message in history]

        filtered_arguments = {
            self.agent_variable_name: agent.name or agent.id,
            self.history_variable_name: messages,
        }

        extracted_settings = {key: setting.model_dump() for key, setting in execution_settings.items()}

        combined_arguments = {
            **original_arguments,
            **extracted_settings,
            **{k: v for k, v in filtered_arguments.items()},
        }

        arguments = KernelArguments(
            **combined_arguments,
        )

        logger.info(f"should_agent_terminate, function invoking: `{self.function.fully_qualified_name}`")

        result = await self.function.invoke(kernel=self.kernel, arguments=arguments)

        if result is None:
            logger.info(
                f"should_agent_terminate, function `{self.function.fully_qualified_name}` invoked with result `None`",
            )
            return False

        logger.info(
            f"should_agent_terminate, function `{self.function.fully_qualified_name}` "
            f"invoked with result `{result.value if result.value else None}`",
        )

        result_parsed = self.result_parser(result)
        if isawaitable(result_parsed):
            result_parsed = await result_parsed
        return result_parsed
