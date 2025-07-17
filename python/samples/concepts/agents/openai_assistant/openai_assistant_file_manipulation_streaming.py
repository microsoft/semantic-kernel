# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from samples.concepts.agents.openai_assistant.openai_assistant_sample_utils import download_response_files
from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings
from semantic_kernel.contents import ChatMessageContent, StreamingAnnotationContent

"""
The following sample demonstrates how to create an Azure Assistant Agent 
to leverage the assistant's ability to have the code interpreter work with
uploaded files. This sample uses streaming responses.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

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
        model=AzureOpenAISettings().chat_deployment_name,
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

    # Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    try:
        user_inputs = [
            # "Which segment had the most sales?",
            # "List the top 5 countries that generated the most profit.",
            "Create a tab delimited file report of profit by each country per month.",
        ]
        for user_input in user_inputs:
            print(f"# User: '{user_input}'")
            annotations: list[StreamingAnnotationContent] = []
            messages: list[ChatMessageContent] = []
            is_code = False
            last_role = None
            async for response in agent.invoke_stream(messages=user_input, thread=thread):
                thread = response.thread
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
        await thread.delete() if thread else None
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
