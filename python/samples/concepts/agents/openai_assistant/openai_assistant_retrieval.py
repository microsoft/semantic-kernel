# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai import AzureAssistantAgent

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI and retrieve it from
the server to create a new instance of the assistant. This is done by
retrieving the assistant definition from the server using the Assistant's 
ID and creating a new instance of the assistant using the retrieved definition.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="Assistant",
        instructions="You are a helpful assistant answering questions about the world in one sentence.",
    )

    # Store the assistant ID
    assistant_id = definition.id

    # Retrieve the assistant definition from the server based on the assistant ID
    new_asst_definition = await client.beta.assistants.retrieve(assistant_id)

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=new_asst_definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    user_inputs = ["Why is the sky blue?"]

    try:
        for user_input in user_inputs:
            await agent.add_chat_message(thread_id=thread.id, message=user_input)
            print(f"# User: '{user_input}'")
            async for content in agent.invoke(thread_id=thread.id):
                print(f"# {content.role}: {content.content}")
    finally:
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
