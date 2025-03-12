# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from samples.concepts.agents.openai_assistant.openai_assistant_sample_utils import download_response_files
from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI and leverage the
assistant's ability to have the code interpreter work with
uploaded files. This sample uses streaming responses.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    csv_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
        "resources",
        "agent_assistant_file_manipulation",
        "sales.csv",
    )

    # Load the employees PDF file as a FileObject
    with open(csv_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    # Get the code interpreter tool and resources
    code_interpreter_tools, code_interpreter_tool_resources = AzureAssistantAgent.configure_code_interpreter_tool(
        file.id
    )

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="FileManipulation",
        instructions="Find answers to the user's questions in the provided file.",
        tools=code_interpreter_tools,
        tool_resources=code_interpreter_tool_resources,
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    try:
        user_inputs = [
            # "Which segment had the most sales?",
            # "List the top 5 countries that generated the most profit.",
            "Create a tab delimited file report of profit by each country per month.",
        ]
        for user_input in user_inputs:
            await agent.add_chat_message(thread_id=thread.id, message=user_input)

            print(f"# User: '{user_input}'")
            annotations: list[StreamingAnnotationContent] = []
            messages: list[ChatMessageContent] = []
            is_code = False
            last_role = None
            async for response in agent.invoke_stream(thread_id=thread.id, messages=messages):
                current_is_code = response.metadata.get("code", False)

                if current_is_code:
                    if not is_code:
                        print("\n\n```python")
                        is_code = True
                    print(response.content, end="", flush=True)
                else:
                    if is_code:
                        print("\n```")
                        is_code = False
                        last_role = None
                    if hasattr(response, "role") and response.role is not None and last_role != response.role:
                        print(f"\n# {response.role}: ", end="", flush=True)
                        last_role = response.role
                    print(response.content, end="", flush=True)
            if is_code:
                print("```\n")
            else:
                print()

            # Use a sample utility method to download the files to the current working directory
            annotations.extend(
                item for message in messages for item in message.items if isinstance(item, StreamingAnnotationContent)
            )
            await download_response_files(agent, annotations)
            annotations.clear()
    finally:
        await client.files.delete(file.id)
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
