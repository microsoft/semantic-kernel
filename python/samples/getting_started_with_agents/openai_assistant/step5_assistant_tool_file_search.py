# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai import AzureAssistantAgent

"""
The following sample demonstrates how to create an OpenAI
Assistant using either Azure OpenAI or OpenAI and leverage the
assistant's file search functionality.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Configure the file path for the employees PDF
    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
    )

    # Load the employees PDF file as a FileObject
    with open(pdf_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    # Create a vector store specifying the file ID to be used for file search
    vector_store = await client.beta.vector_stores.create(
        name="step4_assistant_file_search",
        file_ids=[file.id],
    )

    file_search_tool, file_search_tool_resources = AzureAssistantAgent.configure_file_search_tool(vector_store.id)

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Find answers to the user's questions in the provided file.",
        name="FileSearch",
        tools=file_search_tool,
        tool_resources=file_search_tool_resources,
    )

    # Create the OpenAIAssistantAgent instance
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    user_inputs = {
        "Who is the youngest employee?",
        "Who works in sales?",
        "I have a customer request, who can help me?",
    }

    try:
        for user_input in user_inputs:
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )

            print(f"# User: '{user_input}'")

            async for content in agent.invoke(thread_id=thread.id):
                print(f"# Agent: {content.content}")
    finally:
        await client.files.delete(file.id)
        await client.beta.vector_stores.delete(vector_store.id)
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
