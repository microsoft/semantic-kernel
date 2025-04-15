# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.contents import ChatHistory

# This sample shows how to retrieve the token usage for a chat completion service response.
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
        response = await chat_completion_service.get_chat_message_content(
            chat_history=chat_history,
            settings=request_settings,
        )
        if response:
            print(f"Mosscap:> {response}")
            if "usage" in response.metadata and response.metadata["usage"]:
                # Not all services return token usage information.
                print(f"[Tokens used: {response.metadata['usage']}]")
                running_total += response.metadata["usage"]
            # Add the chat message to the chat history to keep track of the conversation.
            chat_history.add_message(response)

    print(f"Total tokens used: {running_total}")

    # Sample output:
    # User: Why is the sky blue?
    # Mosscap:> Ah, the azure canopy that stretches above us, a question as timeless as the sky itself! ...
    # [Tokens used: prompt_tokens=83 completion_tokens=201]
    # User: What is the capital of France?
    # Mosscap:> Ah, the capital of France, a city that has captured the hearts and imaginations of countless ...
    # [Tokens used: prompt_tokens=298 completion_tokens=176]
    # Total tokens used: prompt_tokens=381 completion_tokens=377


if __name__ == "__main__":
    asyncio.run(main())
