# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings
from semantic_kernel.contents import StreamingFileReferenceContent

logging.basicConfig(level=logging.ERROR)

"""
The following sample demonstrates how to create a simple,
OpenAI assistant agent that utilizes the code interpreter
to analyze uploaded files.

This is the full code sample for the Semantic Kernel Learn Site: How-To: Open AI Assistant Agent Code Interpreter

https://learn.microsoft.com/semantic-kernel/frameworks/agent/examples/example-assistant-code?pivots=programming-language-python
"""  # noqa: E501

# Let's form the file paths that we will later pass to the assistant
csv_file_path_1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "resources",
    "PopulationByAdmin1.csv",
)

csv_file_path_2 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "resources",
    "PopulationByCountry.csv",
)


async def download_file_content(agent: AzureAssistantAgent, file_id: str):
    try:
        # Fetch the content of the file using the provided method
        response_content = await agent.client.files.content(file_id)

        # Get the current working directory of the file
        current_directory = os.path.dirname(os.path.abspath(__file__))

        # Define the path to save the image in the current directory
        file_path = os.path.join(
            current_directory,  # Use the current directory of the file
            f"{file_id}.png",  # You can modify this to use the actual filename with proper extension
        )

        # Save content to a file asynchronously
        with open(file_path, "wb") as file:
            file.write(response_content.content)

        print(f"File saved to: {file_path}")
    except Exception as e:
        print(f"An error occurred while downloading file {file_id}: {str(e)}")


async def download_response_image(agent: AzureAssistantAgent, file_ids: list[str]):
    if file_ids:
        # Iterate over file_ids and download each one
        for file_id in file_ids:
            await download_file_content(agent, file_id)


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Upload the files to the client
    file_ids: list[str] = []
    for path in [csv_file_path_1, csv_file_path_2]:
        with open(path, "rb") as file:
            file = await client.files.create(file=file, purpose="assistants")
            file_ids.append(file.id)

    # Get the code interpreter tool and resources
    code_interpreter_tools, code_interpreter_tool_resources = AzureAssistantAgent.configure_code_interpreter_tool(
        file_ids=file_ids
    )

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        instructions="""
            Analyze the available data to provide an answer to the user's question.
            Always format response using markdown.
            Always include a numerical index that starts at 1 for any lists or tables.
            Always sort lists in ascending order.
            """,
        name="SampleAssistantAgent",
        tools=code_interpreter_tools,
        tool_resources=code_interpreter_tool_resources,
    )

    # Create the agent using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    thread: AssistantAgentThread = None

    try:
        is_complete: bool = False
        file_ids: list[str] = []
        while not is_complete:
            user_input = input("User:> ")
            if not user_input:
                continue

            if user_input.lower() == "exit":
                is_complete = True
                break

            is_code = False
            last_role = None
            async for response in agent.invoke_stream(messages=user_input, thread=thread):
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
                file_ids.extend([
                    item.file_id for item in response.items if isinstance(item, StreamingFileReferenceContent)
                ])
                thread = response.thread
            if is_code:
                print("```\n")
            print()

            await download_response_image(agent, file_ids)
            file_ids.clear()

    finally:
        print("\nCleaning up resources...")
        [await client.files.delete(file_id) for file_id in file_ids]
        await thread.delete() if thread else None
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
