# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import (
    Services,
    get_chat_completion_service_and_request_settings,
)
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent, ImageContent, TextContent

# This sample shows how to create a chatbot that responds to user messages with image input.
# This sample uses the following three main components:
# - a ChatCompletionService: This component is responsible for generating responses to user messages.
# - a ChatHistory: This component is responsible for keeping track of the chat history.
# - an ImageContent: This component is responsible for representing image content.
# The chatbot in this sample is called Mosscap.

# You can select from the following chat completion services:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# - Services.AZURE_AI_INFERENCE
# - Services.ANTHROPIC
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.MISTRAL_AI
# - Services.OLLAMA
# - Services.ONNX
# - Services.VERTEX_AI
# Please make sure you have configured your environment correctly for the selected chat completion service.

# [NOTE]
# Not all models support image input. Make sure to select a model that supports image input.
# Not all services support image input from an image URI. If your image is saved in a remote location,
# make sure to use a service that supports image input from a URI.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

IMAGE_URI = "https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg"
IMAGE_PATH = "samples/concepts/resources/sample_image.jpg"

# Create an image content with the image URI.
image_content_remote = ImageContent(uri=IMAGE_URI)
# You can also create an image content with a local image path.
image_content_local = ImageContent.from_image_file(IMAGE_PATH)


# This is the system message that gives the chatbot its personality.
system_message = """
You are an image reviewing chat bot. Your name is Mosscap and you have one goal critiquing images that are supplied.
"""

# Create a chat history object with the system message and an initial user message with an image input.
chat_history = ChatHistory(system_message=system_message)
chat_history.add_message(
    ChatMessageContent(
        role=AuthorRole.USER,
        items=[TextContent(text="What is in this image?"), image_content_local],
    )
)


async def chat(skip_user_input: bool = False) -> bool:
    """Chat with the chatbot.

    Args:
        skip_user_input (bool): Whether to skip user input. Defaults to False.
    """
    if not skip_user_input:
        try:
            user_input = input("User:> ")
        except KeyboardInterrupt:
            print("\n\nExiting chat...")
            return False
        except EOFError:
            print("\n\nExiting chat...")
            return False

        if user_input == "exit":
            print("\n\nExiting chat...")
            return False

        # Add the user message to the chat history so that the chatbot can respond to it.
        chat_history.add_user_message(user_input)

    # Get the chat message content from the chat completion service.
    response = await chat_completion_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
    )
    if response:
        print(f"Mosscap:> {response}")

        # Add the chat message to the chat history to keep track of the conversation.
        chat_history.add_message(response)

    return True


async def main() -> None:
    # Start the chat with the image input.
    await chat(skip_user_input=True)
    # Continue the chat. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # Mosscap:> The image features a large, historic building that exhibits a traditional half-timbered architectural
    #           style. The structure is located near a dense forest, characterized by lush green trees. The sky above
    #           is partly cloudy, suggesting a pleasant day. The building itself appears well-maintained, with distinct
    #           features such as a turret or spire and decorative wood framing, creating an elegant and charming
    #           appearance in its natural setting.
    # User:> What do you think about the composition of the photo?
    # Mosscap:> The composition of the photo is quite effective. Here are a few observations:
    #           1. **Framing**: The building is positioned slightly off-center, which can create a more dynamic and
    #           engaging image. This drawing of attention to the structure, while still showcasing the surrounding
    #           landscape.
    #           2. **Foreground and Background**: The green foliage and trees in the foreground provide a nice contrast
    #           to the building, enhancing its visual appeal. The dense forest in the background adds depth and context
    #           to the scene.
    #           3. **Lighting**: The light appears to be favorable, suggesting a well-lit scene. The clouds add texture
    #           to the sky without overwhelming the overall brightness.
    #           4. **Perspective**: The angle from which the photo is taken allows viewers to appreciate both the
    #           architecture of the building and its natural environment, creating a harmonious balance.
    #           Overall, the composition successfully highlights the building while incorporating its natural
    #           surroundings, inviting viewers to appreciate both elements together.


if __name__ == "__main__":
    asyncio.run(main())
