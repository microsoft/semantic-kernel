# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai import AzureAssistantAgent

"""
The following sample demonstrates how to create an OpenAI
Assistant using either Azure OpenAI or OpenAI and leverage the
assistant's file search functionality.
"""

# Simulate a conversation with the agent
USER_INPUTS = {
    "Who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
}


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # 2. Read and upload the file to the Azure OpenAI assistant service
    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
    )

    with open(pdf_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    vector_store = await client.beta.vector_stores.create(
        name="step4_assistant_file_search",
        file_ids=[file.id],
    )

    # 3. Create file search tool with uploaded resources
    file_search_tool, file_search_tool_resources = AzureAssistantAgent.configure_file_search_tool(vector_store.id)

    # 4. Create the assistant on the Azure OpenAI service with the file search tool
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Find answers to the user's questions in the provided file.",
        name="FileSearch",
        tools=file_search_tool,
        tool_resources=file_search_tool_resources,
    )

    # 5. Create a Semantic Kernel agent for the Azure OpenAI assistant
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # 6. Create a new thread on the Azure OpenAI assistant service
    thread = await agent.client.beta.threads.create()

    try:
        for user_input in USER_INPUTS:
            # 7. Add the user input to the chat thread
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )
            print(f"# User: '{user_input}'")
            # 8. Invoke the agent for the current thread and print the response
            async for content in agent.invoke(thread_id=thread.id):
                print(f"# Agent: {content.content}")
    finally:
        # 9. Clean up the resources
        await client.files.delete(file.id)
        await client.beta.vector_stores.delete(vector_store.id)
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
