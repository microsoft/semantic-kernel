# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import Agent, ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

"""
The following sample demonstrates how to create a sequential orchestration for
executing multiple agents in sequence, i.e. the output of one agent is the input
to the next agent.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a sequential orchestration, invoking the orchestration, and finally waiting for the
results.
"""


def get_agents() -> list[Agent]:
    """Return a list of agents that will participate in the sequential orchestration.

    Feel free to add or remove agents.
    """
    concept_extractor_agent = ChatCompletionAgent(
        name="ConceptExtractorAgent",
        instructions=(
            "You are a marketing analyst. Given a product description, identify:\n"
            "- Key features\n"
            "- Target audience\n"
            "- Unique selling points\n\n"
        ),
        service=AzureChatCompletion(),
    )
    writer_agent = ChatCompletionAgent(
        name="WriterAgent",
        instructions=(
            "You are a marketing copywriter. Given a block of text describing features, audience, and USPs, "
            "compose a compelling marketing copy (like a newsletter section) that highlights these points. "
            "Output should be short (around 150 words), output just the copy as a single text block."
        ),
        service=AzureChatCompletion(),
    )
    format_proof_agent = ChatCompletionAgent(
        name="FormatProofAgent",
        instructions=(
            "You are an editor. Given the draft copy, correct grammar, improve clarity, ensure consistent tone, "
            "give format and make it polished. Output the final improved copy as a single text block."
        ),
        service=AzureChatCompletion(),
    )

    # The order of the agents in the list will be the order in which they are executed
    return [concept_extractor_agent, writer_agent, format_proof_agent]


# Flag to indicate if a new message is being received
is_new_message = True


def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """Observer function to print the messages from the agents.

    Args:
        message (StreamingChatMessageContent): The streaming message content from the agent.
        is_final (bool): Indicates if this is the final part of the message.
    """
    global is_new_message
    if is_new_message:
        print(f"# {message.name}")
        is_new_message = False
    print(message.content, end="", flush=True)
    if is_final:
        print()
        is_new_message = True


async def main():
    """Main function to run the agents."""
    # 1. Create a sequential orchestration with multiple agents and an agent
    #    response callback to observe the output from each agent as they stream
    #    their responses.
    agents = get_agents()
    sequential_orchestration = SequentialOrchestration(
        members=agents,
        streaming_agent_response_callback=streaming_agent_response_callback,
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
    **Key Features:**
    - Made from eco-friendly stainless steel
    - Insulation technology that keeps drinks cold for up to 24 hours
    - Reusable design, promoting sustainability
    - Possible variations in sizes and colors

    **Target Audience:**
    - Environmentally conscious consumers
    - Active individuals and outdoor enthusiasts
    - Health-conscious individuals looking to stay hydrated
    - Students and professionals looking for stylish and functional drinkware

    **Unique Selling Points:**
    - Combines eco-friendliness with high performance in temperature retention
    - Durable and reusable, reducing reliance on single-use plastics
    - Sleek design that appeals to modern aesthetics while being functional
    - Supporting sustainability initiatives through responsible manufacturing practices
    # WriterAgent
    Sip sustainably with our eco-friendly stainless steel water bottles, designed for the conscious consumer who values
    both performance and aesthetics. Our bottles feature advanced insulation technology that keeps your drinks icy cold
    for up to 24 hours, making them perfect for outdoor adventures, gym sessions, or a busy day at the office. Choose
    from various sizes and stunning colors to match your personal style while making a positive impact on the planet.
    Each reusable bottle helps reduce single-use plastics, supporting a cleaner, greener world. Join the movement toward
    sustainability without compromising on style or functionality. Stay hydrated, look great, and make a difference—get
    your eco-friendly water bottle today!
    # FormatProofAgent
    Sip sustainably with our eco-friendly stainless steel water bottles, designed for the conscious consumer who values
    both performance and aesthetics. Our bottles utilize advanced insulation technology to keep your beverages icy cold
    for up to 24 hours, making them perfect for outdoor adventures, gym sessions, or a busy day at the office. 

    Choose from a variety of sizes and stunning colors to match your personal style while positively impacting the
    planet. Each reusable bottle helps reduce single-use plastics, supporting a cleaner, greener world. 

    Join the movement towards sustainability without compromising on style or functionality. Stay hydrated, look great,
    and make a difference—get your eco-friendly water bottle today!
    ***** Final Result *****
    Sip sustainably with our eco-friendly stainless steel water bottles, designed for the conscious consumer who values
    both performance and aesthetics. Our bottles utilize advanced insulation technology to keep your beverages icy cold
    for up to 24 hours, making them perfect for outdoor adventures, gym sessions, or a busy day at the office.

    Choose from a variety of sizes and stunning colors to match your personal style while positively impacting the
    planet. Each reusable bottle helps reduce single-use plastics, supporting a cleaner, greener world.

    Join the movement towards sustainability without compromising on style or functionality. Stay hydrated, look great,
    and make a difference—get your eco-friendly water bottle today!
    """


if __name__ == "__main__":
    asyncio.run(main())
