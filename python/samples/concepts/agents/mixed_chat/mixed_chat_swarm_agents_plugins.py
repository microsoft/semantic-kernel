# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from semantic_kernel.agents import Agent, AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents import FunctionResultContent, TextContent
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI Swarm   #
# Agent Networking using Semantic Kernel                            #
#####################################################################

PLANNER_INSTRUCTIONS = """You are a research planning coordinator.
    Coordinate market research by delegating to specialized agents:
    - Financial Analyst: For stock data analysis
    - News Analyst: For news gathering and analysis
    - Writer: For compiling final report
    Always send your plan first, then handoff to appropriate agent.
    Always handoff to a single agent at a time.
    Just say TERMINATE when research is complete."""

FINANCIAL_INSTRUCTIONS = """You are a financial analyst.
    Analyze stock market data using the get_stock_data tool.
    Provide insights on financial metrics.
    Always handoff back to planner when analysis is complete."""

NEWS_INSTRUCTIONS = """You are a news analyst.
    Gather and analyze relevant news using the get_news tool.
    Summarize key market insights from news.
    Always handoff back to planner when analysis is complete."""

WRITER_INSTRUCTIONS = """You are a financial report writer.
    Compile research findings into clear, concise reports.
    Always handoff back to planner when writing is complete."""


class NewsPlugin:
    """A sample News Plugin used for the concept sample."""

    @kernel_function(description="Refund an item.")
    def get_news(self, query: str):
        """Get recent news articles about a company"""
        return [
            {
                "title": "Microsoft's Quantum Breakthrough",
                "date": "2025-02-25",
                "summary": (
                    "Microsoft’s Majorana chips mark a groundbreaking quantum computing breakthrough, "
                    "potentially bringing practical quantum computers closer to reality."
                ),
            },
            {
                "title": "MSFT Earnings Release FY25 Q2",
                "date": "2025-01-29",
                "summary": (
                    "Revenue was $69.6 billion and increased 12%."
                    "Operating income was $31.7 billion and increased 17% (up 16% in constant currency)"
                    "Net income was $24.1 billion and increased 10%"
                    "Diluted earnings per share was $3.23 and increased 10%"
                ),
            },
        ]


class StockPlugin:
    """A sample Stock Plugin used for the concept sample."""

    @kernel_function(description="Get stock data.")
    def get_stock_data(self, symbol: str):
        """Get stock data for a given ticker"""
        return {"price": 396.25, "volume": "32.85 Mil", "market_cap": "2951.22 Bil"}


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "terminate" in history[-1].content.lower()


class SwarmSelectionStrategy(SelectionStrategy):
    """Swarm Agent Strategy, Agents are selected with FunctionCalls that return an Agent Type."""

    current_agent: Agent | None = None

    async def select_agent(
        self,
        agents: list["Agent"],
        history: list["ChatMessageContent"],
    ) -> "Agent":
        """Select the next agent in a swarm fashion.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The agent who takes the next turn.
        """
        # In the first iteration return the first agent
        if len(history) <= 1:
            self.current_agent = agents[0]
            return agents[0]

        # Pick the agent from the last message if it was a function call
        # that returned an agent, if not, return the current agent
        agent = self.get_agent_from_last_function_call(history[-1].items)
        self.current_agent = agent
        return agent

    def get_agent_from_last_function_call(self, content: list["ITEM_TYPES"]) -> "Agent":
        """Get the agent from the last function call in the history."""
        for item in content:
            if isinstance(item, FunctionResultContent) and isinstance(item.result, Agent):
                return item.result
        if self.current_agent is None:
            raise AgentChatException("No agent found in the last function call and no current agent set.")
        return self.current_agent


# Intercept Function Calling Flow when another Agent should be called
async def filter_agent_call(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Coroutine[Any, Any, None]],
):
    await next(context)
    if isinstance(context.function_result.value, Agent):
        context.terminate = True
    return


# Create a kernel with a chat completion service and plugins
# Add Filter to stop when other Agents are called
def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, filter_agent_call)
    return kernel


# Add handoff functions to the agents
def _add_agent_handoffs(agent: Agent, agent_handoff: list[Agent]):
    for handoff in agent_handoff:
        _add_handoff(agent.kernel, handoff)


# Add a Handoff as KernelFunction/FunctionCall to the Kernel
def _add_handoff(kernel: Kernel, agent_handoff: Agent):
    @kernel_function(name=f"TransferTo{agent_handoff.name}", description=f"Handoff to {agent_handoff.name}")
    def handoff() -> Agent:
        return agent_handoff

    kernel.add_function(plugin_name=f"Handoff{agent_handoff.name}", function=KernelFunctionFromMethod(method=handoff))


# Configure the function choice behavior to auto invoke kernel functions
# Currently Parallel Tool Calls is not supported for the Swarm Approach
settings = AzureChatPromptExecutionSettings()
settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
settings.parallel_tool_calls = False


news_agent = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("News"),
    plugins=[NewsPlugin()],
    name="NewsAgent",
    instructions=NEWS_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

financial_agent = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("Stock"),
    plugins=[StockPlugin()],
    name="StockAgent",
    instructions=FINANCIAL_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

writer_agent = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("Writer"),
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

planner_agent = ChatCompletionAgent(
    name="PlannerAgent",
    kernel=_create_kernel_with_chat_completion("Planner"),
    instructions=PLANNER_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

# Planner can handoff to all agents
_add_agent_handoffs(planner_agent, [news_agent, financial_agent, writer_agent])
# Financial Analyst can handoff to Planner
_add_agent_handoffs(financial_agent, [planner_agent])
# News Analyst can handoff to Planner
_add_agent_handoffs(news_agent, [planner_agent])
# Writer can handoff to Planner
_add_agent_handoffs(writer_agent, [planner_agent])


async def main():
    chat = AgentGroupChat(
        agents=[planner_agent, news_agent, financial_agent, writer_agent],
        selection_strategy=SwarmSelectionStrategy(),
        termination_strategy=ApprovalTerminationStrategy(maximum_iterations=10),
    )

    input = "Conduct market research for MSFT stock"
    await chat.add_chat_message(input)
    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in chat.invoke():
        agent_answer = ""
        for item in content.items:
            if isinstance(item, FunctionResultContent):
                agent_answer = item.name if isinstance(item.result, Agent) else str(item.result)
            if isinstance(item, TextContent):
                agent_answer = item.text
        print(f"# {content.role} - {content.name or '*'}: '{agent_answer}'")


if __name__ == "__main__":
    asyncio.run(main())
