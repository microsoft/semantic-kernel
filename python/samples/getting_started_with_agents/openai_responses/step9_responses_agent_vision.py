# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents import OpenAIResponseAgent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.response_message_content import ResponseMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to create an OpenAI Response Agent.
The sample shows how to have the assistant answer questions about the provided images.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the chat history. Therefore, client code does need to 
maintain the conversation history if conversation context is desired.
"""


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIResponseAgent.setup_resources()

    # 2. Define a file path for an image that will be used in the conversation
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "cat.jpg")

    # 3. Create a Semantic Kernel agent for the OpenAI Response API
    agent = OpenAIResponseAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about the provided images.",
        name="VisionAgent",
    )

    # 3. Create a chat history to hold the conversation
    chat_history = ChatHistory()

    # 4. Define a list of user messages that include text and image content for the vision task
    user_messages = [
        ResponseMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Describe this image."),
                ImageContent(
                    uri="https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/New_york_times_square-terabass.jpg/1200px-New_york_times_square-terabass.jpg"
                ),
            ],
        ),
        ResponseMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="What is the main color in this image?"),
                ImageContent(uri="https://upload.wikimedia.org/wikipedia/commons/5/56/White_shark.jpg"),
            ],
        ),
        ResponseMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text="Is there an animal in this image?"),
                ImageContent.from_image_file(file_path),
            ],
        ),
    ]

    for message in user_messages:
        # 5. Add the user input to the chat thread
        chat_history.add_message(message=message)
        print(f"# User: {str(message)}")  # type: ignore
        # 6. Invoke the agent with the current chat history and print the response
        response = await agent.get_response(chat_history=chat_history)
        print(f"# Agent: {response.content}\n")
        # 7. Add the agent's response to the chat history to keep track of the conversation
        chat_history.add_message(response)
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
