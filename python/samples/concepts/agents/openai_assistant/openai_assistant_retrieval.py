# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI and retrieve it from
the server to create a new instance of the assistant. This is done by
retrieving the assistant definition from the server using the Assistant's
ID and creating a new instance of the assistant using the retrieved definition.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
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

    # Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    user_inputs = ["Why is the sky blue?"]

    try:
        for user_input in user_inputs:
            print(f"# User: '{user_input}'")
            async for response in agent.invoke(messages=user_input, thread=thread):
                print(f"# {response.role}: {response.content}")
                thread = response.thread
    finally:
        await thread.delete() if thread else None
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
