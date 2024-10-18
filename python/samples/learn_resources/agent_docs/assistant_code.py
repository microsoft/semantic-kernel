# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

###################################################################
# The following sample demonstrates how to create a simple,       #
# OpenAI assistant agent that utilizes the code interpreter       #
# to analyze uploaded files.                                      #
###################################################################

# Let's form the file paths that we will later pass to the assistant
csv_file_path_1 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "PopulationByAdmin1.csv",
)

csv_file_path_2 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "PopulationByCountry.csv",
)


async def download_file_content(agent, file_id: str):
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


async def download_response_image(agent, file_ids: list[str]):
    if file_ids:
        # Iterate over file_ids and download each one
        for file_id in file_ids:
            await download_file_content(agent, file_id)


async def main():
    agent = await AzureAssistantAgent.create(
        kernel=Kernel(),
        service_id="agent",
        name="SampleAssistantAgent",
        instructions="""
                    Analyze the available data to provide an answer to the user's question.
                    Always format response using markdown.
                    Always include a numerical index that starts at 1 for any lists or tables.
                    Always sort lists in ascending order.
                    """,
        enable_code_interpreter=True,
        code_interpreter_filenames=[csv_file_path_1, csv_file_path_2],
    )

    print("Creating thread...")
    thread_id = await agent.create_thread()

    try:
        is_complete: bool = False
        file_ids: list[str] = []
        while not is_complete:
            user_input = input("User:> ")
            if not user_input:
                continue

            if user_input.lower() == "exit":
                is_complete = True

            await agent.add_chat_message(
                thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
            )
            is_code: bool = False
            async for response in agent.invoke_stream(thread_id=thread_id):
                if is_code != response.metadata.get("code"):
                    print()
                    is_code = not is_code

                print(f"{response.content}", end="", flush=True)

                file_ids.extend([
                    item.file_id for item in response.items if isinstance(item, StreamingFileReferenceContent)
                ])

            print()

            await download_response_image(agent, file_ids)
            file_ids.clear()

    finally:
        print("Cleaning up resources...")
        if agent is not None:
            [await agent.delete_file(file_id) for file_id in agent.code_interpreter_file_ids]
            await agent.delete_thread(thread_id)
            await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
