# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

# This sample shows how to retrieve the token usage for a chat completion service streaming response.
# This sample uses the following two main components:
# - a ChatCompletionService: This component is responsible for generating responses to user messages.
# - a ChatHistory: This component is responsible for keeping track of the chat history.


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
# - Services.DEEPSEEK
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.OPENAI)

# This is the system message that gives the chatbot its personality.
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

USER_INPUTS = [
    "Why is the sky blue?",
    "What is the capital of France?",
]

# Create a chat history object with the system message.
chat_history = ChatHistory(system_message=system_message)


async def main() -> None:
    running_total: CompletionUsage = CompletionUsage()

    for user_input in USER_INPUTS:
        print(f"User: {user_input}")
        # Add the user message to the chat history so that the chatbot can respond to it.
        chat_history.add_user_message(user_input)

        # Get the chat message content from the chat completion service.
        response = chat_completion_service.get_streaming_chat_message_content(
            chat_history=chat_history,
            settings=request_settings,
        )

        chunks: list[StreamingChatMessageContent] = []
        print("Mosscap:> ", end="")
        async for chunk in response:
            if chunk:
                print(chunk, end="")
                chunks.append(chunk)
                if "usage" in chunk.metadata and chunk.metadata["usage"]:
                    # Not all services return token usage information.
                    # The usage information is usually available in the last chunk.
                    print(f"\n[Tokens used: {chunk.metadata['usage']}]")
                    running_total += chunk.metadata["usage"]

        # Combine the chunks into a single message to add to the chat history.
        full_message = sum(chunks[1:], chunks[0])
        # Add the chat message to the chat history to keep track of the conversation.
        chat_history.add_message(full_message)

    print(f"Total tokens used: {running_total}")

    # Sample output:
    # User: Why is the sky blue?
    # Mosscap:> Ah, the azure expanse above us, a daily wonder that graces our eyes! The sky's enchanting hue is ...
    # [Tokens used: prompt_tokens=83 completion_tokens=226]
    # User: What is the capital of France?
    # Mosscap:> Ah, the capital of France, a city that embodies the very essence of romance, art, and history—Paris! ...
    # [Tokens used: prompt_tokens=323 completion_tokens=198]
    # Total tokens used: prompt_tokens=406 completion_tokens=424


if __name__ == "__main__":
    asyncio.run(main())
