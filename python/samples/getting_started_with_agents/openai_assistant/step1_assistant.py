# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai import AzureAssistantAgent

"""
The following sample demonstrates how to create an OpenAI assistant using either
Azure OpenAI or OpenAI. The sample shows how to have the assistant answrer
questions about the world.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""

# Simulate a conversation with the agent
USER_INPUTS = [
    "Why is the sky blue?",
    "What is the speed of light?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # 2. Create the assistant on the Azure OpenAI service
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Answer questions about the world in one sentence.",
        name="Assistant",
    )

    # 3. Create a Semantic Kernel agent for the Azure OpenAI assistant
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # 4. Create a new thread on the Azure OpenAI assistant service
    thread = await agent.client.beta.threads.create()

    try:
        for user_input in USER_INPUTS:
            # 5. Add the user input to the chat thread
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )
            print(f"# User: '{user_input}'")
            # 6. Invoke the agent for the current thread and print the response
            response = await agent.get_response(thread_id=thread.id)
            print(f"# {response.name}: {response.content}")

    finally:
        # 7. Clean up the resources
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
