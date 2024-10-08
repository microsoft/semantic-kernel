# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# multi-modal content types to have the assistant describe images   #
# and answer questions about them.                                  #
#####################################################################

HOST_NAME = "Host"
HOST_INSTRUCTIONS = "Answer questions about the menu."


def create_message_with_image_url(input: str, url: str) -> ChatMessageContent:
    return ChatMessageContent(
        role=AuthorRole.USER,
        items=[TextContent(text=input), ImageContent(uri=url)],
    )


def create_message_with_image_reference(input: str, file_id: str) -> ChatMessageContent:
    return ChatMessageContent(
        role=AuthorRole.USER,
        items=[TextContent(text=input), FileReferenceContent(file_id=file_id)],
    )


streaming = False


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, message: ChatMessageContent) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=message)

    print(f"# {AuthorRole.USER}: '{message.items[0].text}'")

    if streaming:
        first_chunk = True
        async for content in agent.invoke_stream(thread_id=thread_id):
            if content.role != AuthorRole.TOOL:
                if first_chunk:
                    print(f"# {content.role}: ", end="", flush=True)
                    first_chunk = False
                print(content.content, end="", flush=True)
        print()
    else:
        async for content in agent.invoke(thread_id=thread_id):
            if content.role != AuthorRole.TOOL:
                print(f"# {content.role}: {content.content}")


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    service_id = "agent"

    # Create the Assistant Agent
    agent = await OpenAIAssistantAgent.create(
        kernel=kernel, service_id=service_id, name=HOST_NAME, instructions=HOST_INSTRUCTIONS
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

    try:
        await invoke_agent(
            agent,
            thread_id=thread_id,
            message=create_message_with_image_url(
                "Describe this image.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg",
            ),
        )
        await invoke_agent(
            agent,
            thread_id=thread_id,
            message=create_message_with_image_url(
                "What is the main color in this image?",
                "https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg",
            ),
        )
        await invoke_agent(
            agent,
            thread_id=thread_id,
            message=create_message_with_image_reference("Is there an animal in this image?", file_id),
        )
    finally:
        await agent.delete_file(file_id)
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
