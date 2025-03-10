# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FileReferenceContent, ImageContent, TextContent

"""
The following sample demonstrates how to create an OpenAI         
assistant using OpenAI configuration, and leverage the
multi-modal content types to have the assistant describe images
and answer questions about them. This sample uses non-streaming responses.
"""


async def main():
    # 1. Create the OpenAI Assistant Agent client
    # Note Azure OpenAI doesn't support vision files yet
    client, model = OpenAIAssistantAgent.setup_resources()

    # 2. Load a sample image of a cat used for the assistant to describe
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "cat.jpg")

    with open(file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    # 3. Create the assistant on the OpenAI service
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Answer questions about the provided images.",
        name="Vision",
    )

    # 4. Create a Semantic Kernel agent for the OpenAI assistant
    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    # 5. Create a new thread on the OpenAI assistant service
    thread = await agent.client.beta.threads.create()

    # 6. Define the user messages with the image content to simulate the conversation
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
            # 7. Add the user input to the chat thread
            await agent.add_chat_message(thread_id=thread.id, message=message)
            print(f"# User: {str(message)}")  # type: ignore
            # 8. Invoke the agent for the current thread and print the response
            async for content in agent.invoke(thread_id=thread.id):
                print(f"# Agent: {content.content}\n")
    finally:
        # 9. Clean up the resources
        await client.files.delete(file.id)
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(assistant_id=agent.id)


if __name__ == "__main__":
    asyncio.run(main())
