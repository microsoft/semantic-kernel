# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory

"""
This sample demonstrates an example of how to use reasoning models using the Azure AI Inference service.
"""

chat_service = AzureAIInferenceChatCompletion(
    ai_model_id="gpt-5-mini",
    # You must specify the endpoint and api_key or configure them via environment variables:
    # AZURE_AI_INFERENCE_ENDPOINT
    # AZURE_AI_INFERENCE_API_KEY
    endpoint="...",
    api_key="...",
)
request_settings = AzureAIInferenceChatPromptExecutionSettings(
    extra_parameters={
        "reasoning_effort": "medium",
        "verbosity": "medium",
    },
)

# Create a ChatHistory object
chat_history = ChatHistory()

# This is the system message that gives the chatbot its personality.
developer_message = """
As an assistant supporting the user,
you recognize all user input
as questions or consultations and answer them.
"""
# The developer message was newly introduced for reasoning models such as OpenAI’s o1 and o1-mini.
# `system message` cannot be used with reasoning models.
chat_history.add_developer_message(developer_message)


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

    chat_history.add_user_message(user_input)

    # Get the chat message content from the chat completion service.
    response = await chat_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
    )
    if response:
        print(f"Reasoning model:> {response}")

        # Add the chat message to the chat history to keep track of the conversation.
        chat_history.add_message(response)

    return True


async def main() -> None:
    # Start the chat loop. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # User:> Why is the sky blue in one sentence?
    # Mosscap:> The sky appears blue because air molecules in the atmosphere scatter shorter-wavelength (blue)
    #           light more efficiently than longer-wavelength (red) light.


if __name__ == "__main__":
    asyncio.run(main())
