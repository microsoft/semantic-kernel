# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai import AzureAssistantAgent

"""
The following sample demonstrates how to create an OpenAI         
assistant using either Azure OpenAI or OpenAI. The sample
shows how to have the assistant answrer questions about 
the world.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Answer questions about the world in one sentence.",
        name="Assistant",
    )

    # Create the agent using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    user_inputs = [
        "Why is the sky blue?",
        "What is the speed of light?",
    ]

    try:
        for user_input in user_inputs:
            # Add the user input to the chat thread
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )
            print(f"# User: '{user_input}'")
            # Invoke the agent for the current thread and print the response
            async for content in agent.invoke(thread_id=thread.id):
                print(f"# Agent: {content.content}")

    finally:
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(assistant_id=agent.id)

    """
    You should see output similar to the following:

    # User: 'Why is the sky blue?'
    # Agent: The sky appears blue because molecules in the atmosphere scatter sunlight in all directions, and blue 
        light is scattered more than other colors because it travels in shorter, smaller waves.
    # User: 'What is the speed of light?'
    # Agent: The speed of light in a vacuum is approximately 299,792,458 meters per second 
        (about 186,282 miles per second).
     """


if __name__ == "__main__":
    asyncio.run(main())
