# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant's ability to have the code interpreter work with        #
# uploaded files.                                                   #
#####################################################################

AGENT_NAME = "FileManipulation"
AGENT_INSTRUCTIONS = "Find answers to the user's questions in the provided file."


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=input))

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(thread_id=thread_id):
        if content.metadata.get("code", False):
            print(f"# {content.role}:\n\n```python")
            print(content.content)
            print("```")
        else:
            print(f"# {content.role}: {content.content}")

        if content.items:
            for item in content.items:
                if isinstance(item, AnnotationContent):
                    print(f"\n`{item.quote}` => {item.file_id}")
                    response_content = await agent.client.files.content(item.file_id)
                    print(response_content.text)


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Get the path to the sales.csv file
    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "agent_assistant_file_manipulation",
        "sales.csv",
    )

    try:
        # Create the assistant agent
        agent = await AzureAssistantAgent.create(
            kernel=kernel,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_code_interpreter=True,
            code_interpreter_filenames=[csv_file_path],
        )

        # Create a thread and specify the file to use for code interpretation
        thread_id = await agent.create_thread()

        user_inputs = [
            "Which segment had the most sales?",
            "List the top 5 countries that generated the most profit.",
            "Create a tab delimited file report of profit by each country per month.",
        ]

        for input in user_inputs:
            await invoke_agent(agent, thread_id=thread_id, input=input)
    finally:
        if agent is not None:
            [await agent.delete_file(file_id) for file_id in agent.code_interpreter_file_ids]
            await agent.delete_thread(thread_id)
            await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
