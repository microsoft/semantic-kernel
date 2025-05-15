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
        instructions=("You are a Researcher. You find information."),
        service=OpenAIChatCompletion(ai_model_id="gpt-4o-search-preview"),
    )

    # Create an OpenAI Assistant agent with code interpreter capability
    client, model = OpenAIAssistantAgent.setup_resources()
    code_interpreter_tool, code_interpreter_tool_resources = OpenAIAssistantAgent.configure_code_interpreter_tool()
    definition = await client.beta.assistants.create(
        model=model,
        name="CoderAgent",
        description="A helpful assistant with code interpreter capability.",
        instructions="You solve questions using code.",
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
            "What are the 50 tallest buildings in the world? Create a table with their names"
            " and heights grouped by country with a column of the average height of the buildings"
            " in each country."
        ),
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(value)

    # 5. Stop the runtime when idle
    await runtime.stop_when_idle()

    """
    Sample output:
    **ResearchAgent**
    Based on the available information, here is a list of the 50 tallest buildings in the world, including their names,
    heights, and countries:

    | Rank | Building Name                         | Height (m) | Country                 |
    |------|---------------------------------------|------------|-------------------------|
    | 1    | Burj Khalifa                          | 828        | United Arab Emirates    |
    | 2    | Merdeka 118                           | 679        | Malaysia                |
    | 3    | Shanghai Tower                        | 632        | China                   |
    | 4    | Makkah Royal Clock Tower              | 601        | Saudi Arabia            |
    | 5    | Ping An Finance Center                | 599        | China                   |
    | 6    | Lotte World Tower                     | 555        | South Korea             |
    | 7    | One World Trade Center                | 541        | United States           |
    | 8    | Guangzhou CTF Finance Centre          | 530        | China                   |
    | 9    | Tianjin CTF Finance Centre            | 530        | China                   |
    | 10   | CITIC Tower                           | 528        | China                   |
    | 11   | TAIPEI 101                            | 508        | Taiwan                  |
    | 12   | Shanghai World Financial Center       | 492        | China                   |
    | 13   | International Commerce Centre         | 484        | Hong Kong               |
    | 14   | Wuhan Greenland Center                | 476        | China                   |
    | 15   | Central Park Tower                    | 472        | United States           |
    | 16   | Lakhta Center                         | 462        | Russia                  |
    | 17   | Vincom Landmark 81                    | 461        | Vietnam                 |
    | 18   | Changsha IFS Tower T1                 | 452        | China                   |
    | 19   | Petronas Tower 1                      | 452        | Malaysia                |
    | 20   | Petronas Tower 2                      | 452        | Malaysia                |
    | 21   | Suzhou IFS                            | 450        | China                   |
    | 22   | Zifeng Tower                          | 450        | China                   |
    | 23   | The Exchange 106                      | 445        | Malaysia                |
    | 24   | Wuhan Center Tower                    | 443        | China                   |
    | 25   | Willis Tower                          | 442        | United States           |
    | 26   | KK100                                 | 442        | China                   |
    | 27   | Guangzhou International Finance Center| 438        | China                   |
    | 28   | Wuhan Greenland Center                | 438        | China                   |
    | 29   | 432 Park Avenue                       | 425        | United States           |
    | 30   | Marina 101                            | 425        | United Arab Emirates    |
    | 31   | Trump International Hotel & Tower     | 423        | United States           |
    | 32   | Jin Mao Tower                         | 421        | China                   |
    | 33   | Princess Tower                        | 414        | United Arab Emirates    |
    | 34   | Al Hamra Tower                        | 413        | Kuwait                  |
    | 35   | Two International Finance Centre      | 412        | Hong Kong               |
    | 36   | 23 Marina                             | 392        | United Arab Emirates    |
    | 37   | CITIC Plaza                           | 391        | China                   |
    | 38   | Shun Hing Square                      | 384        | China                   |
    | 39   | Eton Place Dalian Tower 1             | 383        | China                   |
    | 40   | Empire State Building                 | 381        | United States           |
    | 41   | Burj Mohammed Bin Rashid              | 381        | United Arab Emirates    |
    | 42   | Elite Residence                       | 380        | United Arab Emirates    |
    | 43   | The Address Boulevard                 | 370        | United Arab Emirates    |
    | 44   | Bank of China Tower                   | 367        | Hong Kong               |
    | 45   | Bank of America Tower                 | 366        | United States           |
    | 46   | St. Regis Chicago                     | 363        | United States           |
    | 47   | Almas Tower                           | 360        | United Arab Emirates    |
    | 48   | Hanking Center                        | 359        | China                   |
    | 49   | Guangzhou Chow Tai Fook Finance Centre| 530        | China                   |
    | 50   | Tianjin Chow Tai Fook Binhai Center   | 530        | China                   |

    *Note: The heights are measured to the architectural top, including spires but excluding antennas, signage, flag
    poles, or other functional or technical equipment.*

    This information is compiled from various sources, including the Council on Tall Buildings and Urban Habitat
    (CTBUH) and other reputable architectural databases.
    **CoderAgent**
    Here's the table of the 50 tallest buildings in the world, grouped by country with the buildings' names, heights,
    and the average height for each country:

    | Country               | Number of Buildings | Average Height (m) | Building Names & Heights                     |
    |-----------------------|---------------------|---------------------|---------------------------------------------|
    | China                 | 21                  | 471.33              | Shanghai Tower (632m), Ping An Finance  ... |
    | Hong Kong             | 3                   | 421.00              | International Commerce Centre (484m), T ... |
    | Kuwait                | 1                   | 413.00              | Al Hamra Tower (413m)                   ... |
    | Malaysia              | 4                   | 507.00              | Merdeka 118 (679m), Petronas Tower 1 (4 ... |
    | Russia                | 1                   | 462.00              | Lakhta Center (462m)                    ... |
    | Saudi Arabia          | 1                   | 601.00              | Makkah Royal Clock Tower (601m)         ... |
    | South Korea           | 1                   | 555.00              | Lotte World Tower (555m)                ... |
    | Taiwan                | 1                   | 508.00              | TAIPEI 101 (508m)                       ... |
    | United Arab Emirates  | 8                   | 443.75              | Burj Khalifa (828m), Marina 101 (425m), ... |
    | United States         | 8                   | 426.63              | One World Trade Center (541m), Central  ... |
    | Vietnam               | 1                   | 461.00              | Vincom Landmark 81 (461m)               ... |

    This table presents a clear summary of tallest building distributions across various countries, along with the 
    average height of skyscrapers present in each region.
    Here's the information you requested regarding the 50 tallest buildings in the world, organized by country. The
    table below includes the names and heights of these buildings, along with the average height for each country:

    | Country               | Number of Buildings | Average Height (m) | Building Names & Heights                     |
    |-----------------------|---------------------|---------------------|---------------------------------------------|
    | China                 | 21                  | 471.33              | Shanghai Tower (632m), Ping An Finance  ... |
    | Hong Kong             | 3                   | 421.00              | International Commerce Centre (484m), T ... |
    | Kuwait                | 1                   | 413.00              | Al Hamra Tower (413m)                   ... |
    | Malaysia              | 4                   | 507.00              | Merdeka 118 (679m), Petronas Tower 1 (4 ... |
    | Russia                | 1                   | 462.00              | Lakhta Center (462m)                    ... |
    | Saudi Arabia          | 1                   | 601.00              | Makkah Royal Clock Tower (601m)         ... |
    | South Korea           | 1                   | 555.00              | Lotte World Tower (555m)                ... |
    | Taiwan                | 1                   | 508.00              | TAIPEI 101 (508m)                       ... |
    | United Arab Emirates  | 8                   | 443.75              | Burj Khalifa (828m), Marina 101 (425m), ... |
    | United States         | 8                   | 426.63              | One World Trade Center (541m), Central  ... |
    | Vietnam               | 1                   | 461.00              | Vincom Landmark 81 (461m)               ... |

    This comprehensive list should give you a clear view of the tallest skyscrapers, showcasing their significant
    presence across the globe. If you have any more questions or need further details, feel free to ask!
    """


if __name__ == "__main__":
    asyncio.run(main())
