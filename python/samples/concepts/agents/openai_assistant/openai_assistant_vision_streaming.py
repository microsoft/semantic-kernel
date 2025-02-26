# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FileReferenceContent, ImageContent, TextContent

"""
The following sample demonstrates how to create an OpenAI         
assistant using either Azure OpenAI or OpenAI and leverage the
multi-modal content types to have the assistant describe images
and answer questions about them and provide streaming responses.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "resources", "cat.jpg"
    )

    with open(file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Answer questions about the menu.",
        name="Host",
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    # Define a series of message with either ImageContent or FileReferenceContent
    user_messages = {
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Describe this image."),
                ImageContent(
                    uri="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg"
                ),
            ],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="What is the main color in this image?"),
                ImageContent(uri="https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"),
            ],
        ),
        ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Is there an animal in this image?"),
                FileReferenceContent(file_id=file.id),
            ],
        ),
    }

    try:
        for message in user_messages:
            await agent.add_chat_message(thread_id=thread.id, message=message)

            print(f"# User: '{message.items[0].text}'")  # type: ignore

            first_chunk = True
            async for content in agent.invoke_stream(thread_id=thread.id):
                if content.role != AuthorRole.TOOL:
                    if first_chunk:
                        print("# Agent: ", end="", flush=True)
                        first_chunk = False
                    print(content.content, end="", flush=True)
            print("\n")

    finally:
        await client.files.delete(file.id)
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(assistant_id=agent.id)


if __name__ == "__main__":
    asyncio.run(main())
