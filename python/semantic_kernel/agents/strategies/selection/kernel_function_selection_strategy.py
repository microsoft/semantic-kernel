# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable
from inspect import isawaitable
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class KernelFunctionSelectionStrategy(SelectionStrategy):
    """Determines agent selection based on the evaluation of a Kernel Function."""

    DEFAULT_AGENT_VARIABLE_NAME: ClassVar[str] = "_agent_"
    DEFAULT_HISTORY_VARIABLE_NAME: ClassVar[str] = "_history_"

    agent_variable_name: str | None = Field(default=DEFAULT_AGENT_VARIABLE_NAME)
    history_variable_name: str | None = Field(default=DEFAULT_HISTORY_VARIABLE_NAME)
    arguments: KernelArguments | None = None
    function: KernelFunction
    kernel: Kernel
    result_parser: Callable[..., str] = Field(default_factory=lambda: (lambda: ""))

    async def next(self, agents: list["Agent"], history: list[ChatMessageContent]) -> "Agent":
        """Check if the agent should terminate.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The next agent to interact with.

        Raises:
            AgentExecutionException: If the strategy fails to execute the function or select the next agent
        """
        original_arguments = self.arguments or KernelArguments()
        execution_settings = original_arguments.execution_settings or {}

        messages = [message.to_dict(role_key="role", content_key="content") for message in history]

        filtered_arguments = {
            self.agent_variable_name: ",".join(agent.name for agent in agents),
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

        logger.info(
            f"Kernel Function Selection Strategy next method called, "
            f"invoking function: {self.function.plugin_name}, {self.function.name}",
        )

        try:
            result = await self.function.invoke(kernel=self.kernel, arguments=arguments)
        except Exception as ex:
            logger.error("Kernel Function Selection Strategy next method failed", exc_info=ex)
            raise AgentExecutionException("Agent Failure - Strategy failed to execute function.") from ex

        logger.info(
            f"Kernel Function Selection Strategy next method completed: "
            f"{self.function.plugin_name}, {self.function.name}, result: {result.value if result else None}",
        )

        agent_name = self.result_parser(result)
        if isawaitable(agent_name):
            agent_name = await agent_name

        if agent_name is None:
            raise AgentExecutionException("Agent Failure - Strategy unable to determine next agent.")

        agent_turn = next((agent for agent in agents if agent.name == agent_name), None)
        if agent_turn is None:
            raise AgentExecutionException(f"Agent Failure - Strategy unable to select next agent: {agent_name}")

        return agent_turn
