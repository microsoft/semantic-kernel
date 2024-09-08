# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

AGENT_NAME = "FileManipulation"
AGENT_INSTRUCTIONS = "Find answers to the user's questions in the provided file."

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = False


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(
        thread_id=thread_id,
        message=ChatMessageContent(role=AuthorRole.USER, content=input),
    )

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(thread_id=thread_id):
        print(f"# {content.role}: {content.content}")

        if len(content.items) > 0:
            for item in content.items:
                if isinstance(item, AnnotationContent):
                    print(f"\n`{item.quote}` => {item.file_id}")
                    response_content = await agent.client.files.content(item.file_id)
                    print(response_content.text)


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
            enable_code_interpreter=True,
        )
    else:
        agent = OpenAIAssistantAgent(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_file_search=True,
            enable_code_interpreter=True,
        )

    # Create the OpenAI assistant
    await agent.create_assistant()

    # Get the path to the sales.csv file
    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
        "agent_assistant_file_manipulation",
        "sales.csv",
    )

    # Upload the file for use with the assistant
    file_id = await agent.add_file(csv_file_path, purpose="assistants")

    # Create a thread and specify the file to use for code interpretation
    thread_id = await agent.create_thread(code_interpreter_file_ids=[file_id])

    try:
        await invoke_agent(
            agent, thread_id=thread_id, input="Which segment had the most sales?"
        )
        await invoke_agent(
            agent,
            thread_id=thread_id,
            input="List the top 5 countries that generated the most profit.",
        )
        await invoke_agent(
            agent,
            thread_id=thread_id,
            input="Create a tab delimited file report of profit by each country per month.",
        )
    finally:
        await agent.client.files.delete(file_id)
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
