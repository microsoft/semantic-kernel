# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.agents.orchestration.concurrent import ConcurrentOrchestration
from semantic_kernel.agents.orchestration.tools import structure_output_transform
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.kernel_pydantic import KernelBaseModel

"""
The following sample demonstrates how to create a concurrent orchestration for
executing multiple agents on the same task in parallel and returning a structured output.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a concurrent orchestration with multiple agents with a structure output transform,
invoking the orchestration, and finally waiting for the results.
"""


class ArticleAnalysis(KernelBaseModel):
    """A model to hold the analysis of an article."""

    themes: list[str]
    sentiments: list[str]
    entities: list[str]


def agents() -> list[Agent]:
    """Return a list of agents that will participate in the concurrent orchestration.

    Feel free to add or remove agents.
    """
    theme_agent = ChatCompletionAgent(
        name="ThemeAgent",
        description="An expert in identifying themes in articles",
        instructions="You are an expert in identifying themes in articles. Given an article, identify the main themes.",
        service=OpenAIChatCompletion(),
    )
    sentiment_agent = ChatCompletionAgent(
        name="SentimentAgent",
        description="An expert in sentiment analysis",
        instructions="You are an expert in sentiment analysis. Given an article, identify the sentiment.",
        service=OpenAIChatCompletion(),
    )
    entity_agent = ChatCompletionAgent(
        name="EntityAgent",
        description="An expert in entity recognition",
        instructions="You are an expert in entity recognition. Given an article, extract the entities.",
        service=OpenAIChatCompletion(),
    )

    return [theme_agent, sentiment_agent, entity_agent]


async def main():
    """Main function to run the agents."""
    # 1. Create a concurrent orchestration with multiple agents
    #    and a structure output transform.
    # To enable structured output, you must specify the output transform
    #   and the generic types for the orchestration.
    # Note: the chat completion service and model provided to the
    #    structure output transform must support structured output.
    concurrent_orchestration = ConcurrentOrchestration[str, ArticleAnalysis](
        members=agents(),
        output_transform=structure_output_transform(ArticleAnalysis, OpenAIChatCompletion()),
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Read the task from a file
    with open(os.path.join(os.path.dirname(__file__), "../resources", "Hamlet_full_play_summary.txt")) as file:
        task = file.read()

    # 4. Invoke the orchestration with a task and the runtime
    orchestration_result = await concurrent_orchestration.invoke(
        task=task,
        runtime=runtime,
    )

    # 5. Wait for the results
    value = await orchestration_result.get(timeout=20)
    if isinstance(value, ArticleAnalysis):
        print(value.model_dump_json(indent=2))
    else:
        print("Unexpected result type:", type(value))

    # 6. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

    """
    Sample output:
    {
    "themes": [
        "Revenge and Justice",
        "Madness",
        "Corruption and Power",
        "Death and Mortality",
        "Appearance vs. Reality",
        "Family and Loyalty"
    ],
    "sentiments": [
        "dark",
        "somber",
        "negative"
    ],
    "entities": [
        "Elsinore Castle",
        "Denmark",
        "Horatio",
        "King Hamlet",
        "Claudius",
        "Queen Gertrude",
        "Prince Hamlet",
        "Rosencrantz",
        "Guildenstern",
        "Polonius",
        "Ophelia",
        "Laertes",
        "England",
        "King of England",
        "France",
        "Osric",
        "Fortinbras",
        "Poland"
    ]
    }
    """


if __name__ == "__main__":
    asyncio.run(main())
