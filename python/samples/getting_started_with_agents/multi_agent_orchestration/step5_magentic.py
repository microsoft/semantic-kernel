# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import (
    Agent,
    ChatCompletionAgent,
    MagenticOrchestration,
    OpenAIAssistantAgent,
    StandardMagenticManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAISettings
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
        # Feel free to explore with other agents that support web search, for example,
        # the `OpenAIResponseAgent` or `AzureAIAgent` with bing grounding.
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-search-preview"),
    )

    # Create an OpenAI Assistant agent with code interpreter capability
    client = OpenAIAssistantAgent.create_client()
    code_interpreter_tool, code_interpreter_tool_resources = OpenAIAssistantAgent.configure_code_interpreter_tool()
    definition = await client.beta.assistants.create(
        model=OpenAISettings().chat_model_id,
        name="CoderAgent",
        description="A helpful assistant that writes and executes code to process and analyze data.",
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
    # Note, the Standard Magentic manager uses prompts that have been tuned very
    # carefully but it accepts custom prompts for advanced users and scenarios.
    # For even more advanced scenarios, you can subclass the MagenticManagerBase
    # and implement your own manager logic.
    # The standard manager also requires a chat completion model that supports
    # structured output.
    magentic_orchestration = MagenticOrchestration(
        members=await agents(),
        manager=StandardMagenticManager(chat_completion_service=OpenAIChatCompletion()),
        agent_response_callback=agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await magentic_orchestration.invoke(
        task=(
            "I am preparing a report on the energy efficiency of different machine learning model architectures. "
            "Compare the estimated training and inference energy consumption of ResNet-50, BERT-base, and GPT-2 "
            "on standard datasets (e.g., ImageNet for ResNet, GLUE for BERT, WebText for GPT-2). "
            "Then, estimate the CO2 emissions associated with each, assuming training on an Azure Standard_NC6s_v3 VM "
            "for 24 hours. Provide tables for clarity, and recommend the most energy-efficient model "
            "per task type (image classification, text classification, and text generation)."
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
    Estimating the energy consumption and associated CO₂ emissions for training and inference of ResNet-50, BERT-base...

    **CoderAgent**
    Here is the comparison of energy consumption and CO₂ emissions for each model (ResNet-50, BERT-base, and GPT-2)
    over a 24-hour period:

    | Model     | Training Energy (kWh) | Inference Energy (kWh) | Total Energy (kWh) | CO₂ Emissions (kg) |
    |-----------|------------------------|------------------------|---------------------|---------------------|
    | ResNet-50 | 21.11                  | 0.08232                | 21.19232            | 19.50               |
    | BERT-base | 0.048                  | 0.23736                | 0.28536             | 0.26                |
    | GPT-2     | 42.22                  | 0.35604                | 42.57604            | 39.17               |

    ### Recommendations:
    ...

    **CoderAgent**
    Here are the recalibrated results for energy consumption and CO₂ emissions, assuming a more conservative approach
    for models like GPT-2:

    | Model            | Training Energy (kWh) | Inference Energy (kWh) | Total Energy (kWh) | CO₂ Emissions (kg) |
    |------------------|------------------------|------------------------|---------------------|---------------------|
    | ResNet-50        | 21.11                  | 0.08232                | 21.19232            | 19.50               |
    | BERT-base        | 0.048                  | 0.23736                | 0.28536             | 0.26                |
    | GPT-2 (Adjusted) | 42.22                  | 0.35604                | 42.57604            | 39.17               |

    ...

    **ResearchAgent**
    Estimating the energy consumption and associated CO₂ emissions for training and inference of machine learning ...

    **ResearchAgent**
    Estimating the energy consumption and CO₂ emissions of training and inference for ResNet-50, BERT-base, and ...

    **CoderAgent**
    Here is the estimated energy use and CO₂ emissions for a full day of operation for each model on an Azure ...

    **ResearchAgent**
    Recent analyses have highlighted the substantial energy consumption and carbon emissions associated with ...

    **CoderAgent**
    Here's the refined estimation for the energy use and CO₂ emissions for optimized models on an Azure ...

    **CoderAgent**
    To provide precise estimates for CO₂ emissions based on Azure's regional data centers' carbon intensity, we need ...

    **ResearchAgent**
    To refine the CO₂ emission estimates for training and inference of ResNet-50, BERT-base, and GPT-2 on an Azure ...

    **CoderAgent**
    Here's the refined comparative table for energy consumption and CO₂ emissions for ResNet-50, BERT-base, and GPT-2,
    taking into account carbon intensity data for Azure's West Europe and Sweden Central regions:

    | Model      | Energy (kWh) | CO₂ Emissions West Europe (kg) | CO₂ Emissions Sweden Central (kg) |
    |------------|--------------|--------------------------------|-----------------------------------|
    | ResNet-50  | 5.76         | 0.639                          | 0.086                            |
    | BERT-base  | 9.18         | 1.019                          | 0.138                            |
    | GPT-2      | 12.96        | 1.439                          | 0.194                            |

    **Refined Recommendations:**

    ...

    Final result:
    Here is the comprehensive report on energy efficiency and CO₂ emissions for ResNet-50, BERT-base, and GPT-2 models
    when trained and inferred on an Azure Standard_NC6s_v3 VM for 24 hours.

    ### Energy Consumption and CO₂ Emissions:

    Based on refined analyses, here are the estimated energy consumption and CO₂ emissions for each model:

    | Model      | Energy (kWh) | CO₂ Emissions West Europe (kg) | CO₂ Emissions Sweden Central (kg) |
    |------------|--------------|--------------------------------|-----------------------------------|
    | ResNet-50  | 5.76         | 0.639                          | 0.086                            |
    | BERT-base  | 9.18         | 1.019                          | 0.138                            |
    | GPT-2      | 12.96        | 1.439                          | 0.194                            |

    ### Recommendations for Energy Efficiency:

    ...
    """


if __name__ == "__main__":
    asyncio.run(main())
