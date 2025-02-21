# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from samples.concepts.agents.assistant_agent.assistant_sample_utils import download_response_files
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents.annotation_content import AnnotationContent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant's ability to have the code interpreter work with        #
# uploaded files.                                                   #
#####################################################################


async def main():
    # Create the OpenAI Assistant Agent
    # client = OpenAIAssistantAgent.create_openai_client()

    # To create an OpenAIAssistantAgent for Azure OpenAI, use the following:
    client = OpenAIAssistantAgent.create_azure_openai_client()

    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "agent_assistant_file_manipulation",
        "sales.csv",
    )

    # Load the employees PDF file as a FileObject
    with open(csv_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model="gpt-4o",
        name="FileManipulation",
        instructions="Find answers to the user's questions in the provided file.",
        tools=[{"type": "code_interpreter"}],
        tool_resources={"code_interpreter": {"file_ids": [file.id]}},
        response_format=
    )

    # Create the OpenAIAssistantAgent instance
    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    try:
        user_inputs = [
            "Which segment had the most sales?",
            "List the top 5 countries that generated the most profit.",
            "Create a tab delimited file report of profit by each country per month.",
        ]

        for input in user_inputs:
            await agent.add_chat_message(thread_id=thread.id, message=input)

            print(f"# User: '{input}'")
            async for content in agent.invoke(thread_id=thread.id):
                if content.metadata.get("code", False):
                    print(f"# {content.role}:\n\n```python")
                    print(content.content)
                    print("```")
                else:
                    print(f"# {content.role}: {content.content}")

                if content.items:
                    for item in content.items:
                        if isinstance(item, AnnotationContent):
                            await download_response_files(agent, [item])
    finally:
        await client.files.delete(file.id)
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
