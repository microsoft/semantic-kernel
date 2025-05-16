# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import Agent, ChatCompletionAgent, MagenticOrchestration, OpenAIAssistantAgent
from semantic_kernel.agents.orchestration.magentic import StandardMagenticManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIPromptExecutionSettings
from semantic_kernel.contents import ChatMessageContent

"""
The following sample demonstrates how to create a Magentic orchestration with two agents:
- A Research agent that can perform web searches
- A Coder agent that can run code using the code interpreter

Read more about Magentic here:
https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/

This sample demonstrates the basic steps of creating and starting a runtime, creating
a Magentic orchestration with two agents and a Magentic manager, invoking the
orchestration, and finally waiting for the results.

The Magentic manager requires a chat completion model that supports structured output.
"""


async def agents() -> list[Agent]:
    """Return a list of agents that will participate in the Magentic orchestration.

    Feel free to add or remove agents.
    """
    research_agent = ChatCompletionAgent(
        name="ResearchAgent",
        description="A helpful assistant with access to web search. Ask it to perform web searches.",
        instructions=(
            "You are a Researcher. You find information without additional computation or quantitative analysis."
        ),
        # This agent requires the gpt-4o-search-preview model to perform web searches.
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-search-preview"),
    )

    # Create an OpenAI Assistant agent with code interpreter capability
    client, model = OpenAIAssistantAgent.setup_resources()
    code_interpreter_tool, code_interpreter_tool_resources = OpenAIAssistantAgent.configure_code_interpreter_tool()
    definition = await client.beta.assistants.create(
        model=model,
        name="CoderAgent",
        description="A helpful assistant with code interpreter capability.",
        instructions="You solve questions using code. Please provide detailed analysis and computation process.",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_tool_resources,
    )
    coder_agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    return [research_agent, coder_agent]


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """Main function to run the agents."""
    # 1. Create a Magentic orchestration with two agents and a Magentic manager
    # Note, the Magentic manager accepts custom prompts for advanced users and scenarios.
    magentic_orchestration = MagenticOrchestration(
        members=await agents(),
        manager=StandardMagenticManager(
            chat_completion_service=OpenAIChatCompletion(),
            prompt_execution_settings=OpenAIPromptExecutionSettings(),
        ),
        agent_response_callback=agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await magentic_orchestration.invoke(
        task=(
            "The 2025 trade war between the US and other countries has had a significant impact "
            "on the global economy. I am a business owner in the US that import household goods "
            "such as bed sheets and holiday decorations from south-east Asia. I want "
            "to know the impact of the tariffs on my business given that my current profit "
            "margin is 20%. And If I were to increase the price of my products by 10%, "
            "how would that affect my customer behavior and profit margin? Base on the analysis, "
            "find similar cases in the past to cross-reference the results. Provide a detailed "
            "report and recommendations on how to adapt to the changing market conditions at the end."
        ),
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()

    print(f"\nFinal result:\n{value}")

    # 5. Stop the runtime when idle
    await runtime.stop_when_idle()

    """
    Sample output:
    **ResearchAgent**
    The 2025 trade war has led to significant tariffs imposed by the United States on imports from Southeast Asian
    countries, directly affecting industries such as household goods. For instance, Cambodia faces a 49% tariff,
    Vietnam 46%, and Thailand 36% on their exports to the U.S.
    ([thailandinfo.se](https://www.thailandinfo.se/en/usa-tariffs-southeast-asia-2025/?utm_source=openai))

    ...
    **CoderAgent**
    Here's the analysis based on your scenario:

    1. **Initial Scenario:**
    - Initial Selling Price: $125.00 (to achieve a 20% profit margin)

    2. **After Applying Tariffs:**
    - New Cost Price: $145.00 (after a 45% tariff on the initial $100 cost)

    3. **With a 10% Price Increase:**
    - New Selling Price: $137.50

    4. **Profit Margin and Volume Impact:**
    ...
    **ResearchAgent**
    In response to increased tariffs during trade wars, various companies have implemented strategic measures to
    mitigate financial impacts and maintain competitiveness. Notable examples include:

    **1. Supply Chain Diversification:**

    - **Steven Madden Ltd.:** Faced with a 10% tariff on handbags imported from China, the company relocated
    production to Cambodia to circumvent the tariffs.([money.usnews.com](https://money.usnews.com/money/blogs/...
    **CoderAgent**
    Here's a detailed simulated report on the potential business impact due to tariffs and price adjustments,
    along with strategic recommendations:

    ### Financial Impact Summary:

    1. **New Cost Price after Tariffs:** $145.00
    2. **New Selling Price after 10% Increase:** $137.50
    3. **New Profit Margin:** -5.45%
    4. **Estimated Sales Volume Change:** Decrease to 95.0% of original
    5. **New Estimated Profit per Unit:** Negative $7.12

    ### Strategies from Historical Cases:
    ...
    """


if __name__ == "__main__":
    asyncio.run(main())
