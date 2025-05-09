# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.agents.orchestration.sequential import SequentialOrchestration
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent

"""
The following sample demonstrates how to create a sequential orchestration for
executing multiple agents in sequence, i.e. the output of one agent is the input
to the next agent.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a sequential orchestration, invoking the orchestration, and finally waiting for the
results.
"""


def agents() -> list[Agent]:
    """Return a list of agents that will participate in the sequential orchestration.

    Feel free to add or remove agents.
    """
    concept_extractor_agent = ChatCompletionAgent(
        name="ConceptExtractorAgent",
        description="A agent that extracts key concepts from a product description.",
        instructions=(
            "You are a marketing analyst. Given a product description, identify:\n"
            "- Key features\n"
            "- Target audience\n"
            "- Unique selling points\n\n"
        ),
        service=OpenAIChatCompletion(),
    )
    writer_agent = ChatCompletionAgent(
        name="WriterAgent",
        description="An agent that writes a marketing copy based on the extracted concepts.",
        instructions=(
            "You are a marketing copywriter. Given a block of text describing features, audience, and USPs, "
            "compose a compelling marketing copy (like a newsletter section) that highlights these points. "
            "Output should be short (around 150 words), output just the copy as a single text block."
        ),
        service=OpenAIChatCompletion(),
    )
    format_proof_agent = ChatCompletionAgent(
        name="FormatProofAgent",
        description="An agent that formats and proofreads the marketing copy.",
        instructions=(
            "You are an editor. Given the draft copy, correct grammar, improve clarity, ensure consistent tone, "
            "give format and make it polished. Output the final improved copy as a single text block."
        ),
        service=OpenAIChatCompletion(),
    )

    # The order of the agents in the list will be the order in which they are executed
    return [concept_extractor_agent, writer_agent, format_proof_agent]


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"# {message.name}\n{message.content}")


async def main():
    """Main function to run the agents."""
    # 1. Create a sequential orchestration with multiple agents and an agent
    #    response callback to observe the output from each agent.
    sequential_orchestration = SequentialOrchestration(
        members=agents(),
        agent_response_callback=agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await sequential_orchestration.invoke(
        task="An eco-friendly stainless steel water bottle that keeps drinks cold for 24 hours",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get(timeout=20)
    print(f"***** Final Result *****\n{value}")

    # 5. Stop the runtime when idle
    await runtime.stop_when_idle()

    """
    Sample output:
    # ConceptExtractorAgent
    - Key Features:
    - Made of eco-friendly stainless steel
    - Keeps drinks cold for 24 hours

    - Target Audience:
    - Environmentally conscious consumers
    - People who need a reliable way to keep their drinks cold for extended periods, such as athletes, travelers, and
        outdoor enthusiasts

    - Unique Selling Points:
    - Environmentally sustainable material
    - Exceptionally long-lasting cold temperature retention (24 hours)
    # WriterAgent
    Keep your beverages refreshingly chilled all day long with our eco-friendly stainless steel bottles. Perfect for
    those who care about the planet, our bottles not only reduce waste but also promise to keep your drinks cold for
    an impressive 24 hours. Whether you're an athlete pushing your limits, a traveler on the go, or simply an outdoor
    enthusiast enjoying nature's beauty, this is the accessory you can't do without. Built from sustainable materials,
    our bottles ensure both environmental responsibility and remarkable performance. Stay refreshed, stay green, and
    make every sip a testament to your planet-friendly lifestyle. Join us in the journey towards a cooler, sustainable
    tomorrow.
    # FormatProofAgent
    Keep your beverages refreshingly chilled all day long with our eco-friendly stainless steel bottles. Perfect for
    those who care about the planet, our bottles not only reduce waste but also promise to keep your drinks cold for
    an impressive 24 hours. Whether you're an athlete pushing your limits, a traveler on the go, or simply an outdoor
    enthusiast enjoying nature's beauty, this is the accessory you can't do without. Built from sustainable materials,
    our bottles ensure both environmental responsibility and remarkable performance. Stay refreshed, stay green, and
    make every sip a testament to your planet-friendly lifestyle. Join us in the journey towards a cooler, sustainable
    tomorrow.
    ***** Final Result *****
    Keep your beverages refreshingly chilled all day long with our eco-friendly stainless steel bottles. Perfect for
    those who care about the planet, our bottles not only reduce waste but also promise to keep your drinks cold for
    an impressive 24 hours. Whether you're an athlete pushing your limits, a traveler on the go, or simply an outdoor
    enthusiast enjoying nature's beauty, this is the accessory you can't do without. Built from sustainable materials,
    our bottles ensure both environmental responsibility and remarkable performance. Stay refreshed, stay green, and
    make every sip a testament to your planet-friendly lifestyle. Join us in the journey towards a cooler, sustainable
    tomorrow.
    """


if __name__ == "__main__":
    asyncio.run(main())
