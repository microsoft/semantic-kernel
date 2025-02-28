# Copyright (c) Microsoft. All rights reserved.

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from semantic_kernel.agents import Agent, AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.selection.swarm_selection_strategy import SwarmSelectionStrategy
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

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

global planner_agent
global financial_agent
global news_agent
global writer_agent


class NewsPlugin:
    """A sample News Plugin used for the concept sample."""

    @kernel_function(description="Refund an item.")
    def get_news(self, query: str):
        """Get recent news articles about a company"""
        return [
            {
                "title": "Tesla Expands Cybertruck Production",
                "date": "2024-03-20",
                "summary": (
                    "Tesla ramps up Cybertruck manufacturing capacity at "
                    "Gigafactory Texas, aiming to meet strong demand."
                ),
            },
            {
                "title": "Tesla FSD Beta Shows Promise",
                "date": "2024-03-19",
                "summary": (
                    "Latest Full Self-Driving beta demonstrates significant "
                    "improvements in urban navigation and safety features."
                ),
            },
            {
                "title": "Model Y Dominates Global EV Sales",
                "date": "2024-03-18",
                "summary": (
                    "Tesla's Model Y becomes best-selling electric vehicle "
                    "worldwide, capturing significant market share."
                ),
            },
        ]


class StockPlugin:
    """A sample Stock Plugin used for the concept sample."""

    @kernel_function(description="Get stock data.")
    def get_stock_data(self, symbol: str):
        """Get stock data for a given ticker"""
        return {"price": 180.25, "volume": 1000000, "pe_ratio": 65.4, "market_cap": "700B"}


# Handoff to other Agents with Function Calling
class HandoffPlanner:
    @kernel_function(description="Planner to Sales Agent")
    def transfer_to_planner(self):
        """Handoff to Planner Agent"""
        return planner_agent


class HandoffNews:
    @kernel_function(description="Handoff to News Agent")
    def transfer_to_news(self):
        """Handoff to News Agent"""
        return news_agent


class HandoffStock:
    @kernel_function(description="Handoff to Stock Agent")
    def transfer_to_stock(self):
        """Handoff to Stock Agent"""
        return financial_agent


class HandoffWriter:
    @kernel_function(description="Handoff to Writer Agent")
    def transfer_to_writer(self):
        """Handoff to Writer Agent"""
        return writer_agent


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "terminate" in history[-1].content.lower()


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
def _create_kernel_with_chat_completion(service_id: str, plugins: list) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, filter_agent_call)
    for plugin in plugins:
        kernel.add_plugin(plugin=plugin, plugin_name=type(plugin).__name__)
    return kernel


# Configure the function choice behavior to auto invoke kernel functions
# Currently Parralel Tool Calls is not supported
settings = AzureChatPromptExecutionSettings()
settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
settings.parallel_tool_calls = False

planner_agent = ChatCompletionAgent(
    name="PlannerAgent",
    kernel=_create_kernel_with_chat_completion("Planner", [HandoffNews(), HandoffStock(), HandoffWriter()]),
    instructions=PLANNER_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

news_agent = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("News", [HandoffPlanner(), NewsPlugin()]),
    name="NewsAgent",
    instructions=NEWS_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

financial_agent = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("Financial", [HandoffPlanner(), StockPlugin()]),
    name="StockAgent",
    instructions=FINANCIAL_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)

writer_agent = ChatCompletionAgent(
    kernel=_create_kernel_with_chat_completion("Writer", [HandoffPlanner()]),
    name="WriterAgent",
    instructions=FINANCIAL_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)


async def main():
    chat = AgentGroupChat(
        agents=[planner_agent, news_agent, financial_agent, writer_agent],
        selection_strategy=SwarmSelectionStrategy(),
        termination_strategy=ApprovalTerminationStrategy(maximum_iterations=10),
    )

    input = "Conduct market research for TSLA stock"
    await chat.add_chat_message(input)
    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in chat.invoke():
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")


if __name__ == "__main__":
    asyncio.run(main())
