# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FileReferenceContent, ImageContent, TextContent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# multi-modal content types to have the assistant describe images   #
# and answer questions about them.                                  #
#####################################################################


# Create the instance of the Kernel
kernel = Kernel()

# Toggle streaming or non-streaming mode
streaming = False


async def main():
    # Create the Assistant Agent
    AGENT_NAME = "Host"
    AGENT_INSTRUCTIONS = "Answer questions about the menu."
    agent = await OpenAIAssistantAgent.create(
        kernel=kernel, service_id="agent", name=AGENT_NAME, instructions=AGENT_INSTRUCTIONS
    )

    cat_image_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources",
        "cat.jpg",
    )

    # Upload the file for use with the assistant
    file_id = await agent.add_file(cat_image_file_path, purpose="vision")

    # Create a thread for the conversation
    thread_id = await agent.create_thread()

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
                FileReferenceContent(file_id=file_id),
            ],
        ),
    }
    try:
        for message in user_messages:
            await agent.add_chat_message(thread_id=thread_id, message=message)

            print(f"# User: '{message.items[0].text}'")

            if streaming:
                first_chunk = True
                async for content in agent.invoke_stream(thread_id=thread_id):
                    if content.role != AuthorRole.TOOL:
                        if first_chunk:
                            print("# Agent: ", end="", flush=True)
                            first_chunk = False
                        print(content.content, end="", flush=True)
                print()
            else:
                async for content in agent.invoke(thread_id=thread_id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")

    finally:
        await agent.delete_file(file_id)
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
