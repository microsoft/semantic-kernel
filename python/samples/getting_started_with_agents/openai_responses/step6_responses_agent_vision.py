# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the agent answer questions about the provided images.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the chat history. Therefore, client code does need to 
maintain the conversation history if conversation context is desired.
"""


async def main():
    # 1. Create the client using OpenAI resources and configuration
    client, model = OpenAIResponsesAgent.setup_resources()

    # 2. Define a file path for an image that will be used in the conversation
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "cat.jpg")

    # 3. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = OpenAIResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about the provided images.",
        name="VisionAgent",
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    # 4. Define a list of user messages that include text and image content for the vision task
    user_messages = [
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
                ImageContent.from_image_file(file_path),
            ],
        ),
    ]

    for user_input in user_messages:
        print(f"# User: {str(user_input)}")  # type: ignore
        # 5. Invoke the agent with the current chat history and print the response
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# Agent: {response.content}\n")
        thread = response.thread
    """
    You should see output similar to the following:

    # User: Describe this image.
    # Agent: The image depicts a bustling scene of Times Square in New York City...

    # User: What is the main color in this image?
    # Agent: The main color in the image is blue.

    # User: Is there an animal in this image?
    # Agent: Yes, there is a cat in the image.
     """


if __name__ == "__main__":
    asyncio.run(main())
