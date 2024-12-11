# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import (
    Services,
    get_chat_completion_service_and_request_settings,
)
from semantic_kernel.contents import ChatHistory, StreamingChatMessageContent

# This sample shows how to create a chatbot that streams responses.
# This sample uses the following two main components:
# - a ChatCompletionService: This component is responsible for generating responses to user messages.
# - a ChatHistory: This component is responsible for keeping track of the chat history.
# The chatbot in this sample is called Mosscap, who responds to user messages with long flowery prose.


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
# Please note that not all models support streaming responses. Make sure to select a model that supports streaming.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

# This is the system message that gives the chatbot its personality.
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

# Create a chat history object with the system message.
chat_history = ChatHistory(system_message=system_message)


async def chat() -> bool:
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
    # The response is an async generator that streams the response in chunks.
    response = chat_completion_service.get_streaming_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
    )

    # Capture the chunks of the response and print them as they come in.
    chunks: list[StreamingChatMessageContent] = []
    print("Mosscap:> ", end="")
    async for chunk in response:
        if chunk:
            chunks.append(chunk)
            print(chunk, end="")
    print("")

    # Combine the chunks into a single message to add to the chat history.
    full_message = sum(chunks[1:], chunks[0])
    # Add the chat message to the chat history to keep track of the conversation.
    chat_history.add_message(full_message)

    return True


async def main() -> None:
    # Start the chat loop. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # User:> Why is the sky blue in one sentence?
    # Mosscap:> The sky is blue due to the scattering of sunlight by the molecules in the Earth's atmosphere,
    #           a phenomenon known as Rayleigh scattering, which causes shorter blue wavelengths to become more
    #           prominent in our visual perception.


if __name__ == "__main__":
    asyncio.run(main())
