# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

AGENT_NAME = "FileSearch"
AGENT_INSTRUCTIONS = "Find answers to the user's questions in the provided file."

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = True


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(
        thread_id=thread_id,
        message=ChatMessageContent(role=AuthorRole.USER, content=input),
    )

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(thread_id=thread_id):
        if content.role != AuthorRole.TOOL:
            print(f"# {content.role}: {content.content}")


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Define a service_id for the sample
    service_id = "agent"

    # Create the agent configuration
    if use_azure_openai:
        agent = AzureAssistantAgent(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_file_search=True,
        )
    else:
        agent = OpenAIAssistantAgent(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_file_search=True,
        )

    # Get the path to the travelinfo.txt file
    txt_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
        "agent_assistant_file_search",
        "travelinfo.txt",
    )

    # Open the file and create the assistant with a vector store ID
    with open(txt_file_path, "rb") as file:
        # Create a file with the travelinfo.txt content
        file = await agent.client.files.create(file=file, purpose="assistants")  # type: ignore

        # Create a vector store with the file ID
        vector_store = await agent.client.beta.vector_stores.create(file_ids=[file.id])

        # Create an assistant with the vector store ID
        await agent.create_assistant(vector_store_id=vector_store.id)

        # Define a thread and invoke the agent with the user input
        thread_id = await agent.create_thread()

        try:
            await invoke_agent(agent, thread_id=thread_id, input="Where did Sam go?")
            await invoke_agent(
                agent, thread_id=thread_id, input="When does the flight leave Seattle?"
            )
            await invoke_agent(
                agent,
                thread_id=thread_id,
                input="What is the hotel contact info at the destination?",
            )
        finally:
            await agent.client.beta.vector_stores.delete(vector_store.id)
            await agent.client.files.delete(file.id)
            await agent.delete_thread(thread_id)
            await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
