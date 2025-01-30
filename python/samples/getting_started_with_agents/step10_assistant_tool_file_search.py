# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import AzureAssistantAgent, OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant's file search functionality.                            #
#####################################################################


# Create the instance of the Kernel
kernel = Kernel()

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = False


async def main():
    # Get the path to the employees.pdf file
    pdf_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources", "employees.pdf")

    # Define a service_id for the sample
    service_id = "agent"
    AGENT_NAME = "FileSearch"
    AGENT_INSTRUCTIONS = "Find answers to the user's questions in the provided file."
    # Create the agent configuration
    if use_azure_openai:
        agent = await AzureAssistantAgent.create(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_file_search=True,
            vector_store_filenames=[pdf_file_path],
        )
    else:
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_file_search=True,
            vector_store_filenames=[pdf_file_path],
        )

    # Define a thread and invoke the agent with the user input
    thread_id = await agent.create_thread()

    user_inputs = {
        "Who is the youngest employee?",
        "Who works in sales?",
        "I have a customer request, who can help me?",
    }

    try:
        for user_input in user_inputs:
            await agent.add_chat_message(
                thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
            )

            print(f"# User: '{user_input}'")

            async for content in agent.invoke(thread_id=thread_id):
                if content.role != AuthorRole.TOOL:
                    print(f"# Agent: {content.content}")
    finally:
        [await agent.delete_file(file_id) for file_id in agent.file_search_file_ids]
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
