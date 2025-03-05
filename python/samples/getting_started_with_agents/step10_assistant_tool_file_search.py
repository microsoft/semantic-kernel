# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant's file search functionality.                            #
#####################################################################


AGENT_NAME = "FileSearch"
AGENT_INSTRUCTIONS = "Find answers to the user's questions in the provided file."

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = True


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=input))

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(thread_id=thread_id):
        if content.role != AuthorRole.TOOL:
            print(f"# {content.role}: {content.content}")


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Define a service_id for the sample
    service_id = "agent"

    # Get the path to the travelinfo.txt file
    pdf_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources", "employees.pdf")

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

    try:
        await invoke_agent(agent, thread_id=thread_id, input="Who is the youngest employee?")
        await invoke_agent(agent, thread_id=thread_id, input="Who works in sales?")
        await invoke_agent(agent, thread_id=thread_id, input="I have a customer request, who can help me?")
    finally:
        [await agent.delete_file(file_id) for file_id in agent.file_search_file_ids]
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
