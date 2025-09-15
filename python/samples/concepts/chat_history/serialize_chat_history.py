# Copyright (c) Microsoft. All rights reserved.

import asyncio
import tempfile

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel.contents import ChatHistory

"""
This sample demonstrates how to build a conversational chatbot
using Semantic Kernel, it features auto function calling,
but with file-based serialization of the chat history.
This sample stores and reads the chat history at every turn.
This is not the best way to do it, but clearly demonstrates the mechanics.
More optimal would for instance be to only write once when a conversation is done.
And writing to something other then a file is also usually better.
"""


# You can select from the following chat completion services that support function calling:
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


async def chat(file) -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        # Try to load the chat history from a file.
        history = ChatHistory.load_chat_history_from_file(file_path=file)
        print(f"Chat history successfully loaded {len(history.messages)} messages.")
    except Exception:
        # Create a new chat history to store the system message, initial messages, and the conversation.
        print("Chat history file not found. Starting a new conversation.")
        history = ChatHistory()
        history.add_system_message(
            "You are a chat bot. Your name is Mosscap and you have one goal: figure out what people need."
        )

    try:
        # Get the user input
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    # Add the user input to the chat history
    history.add_user_message(user_input)
    # Get a response from the chat completion service
    result = await chat_completion_service.get_chat_message_content(history, request_settings)

    # Update the chat history with the user's input and the assistant's response
    if result:
        print(f"Mosscap:> {result}")
        history.add_message(result)

    # Save the chat history to a file.
    print(f"Saving {len(history.messages)} messages to the file.")
    history.store_chat_history_to_file(file_path=file)
    return True


"""
Sample output:

Welcome to the chat bot!
  Type 'exit' to exit.
  Try a math question to see function calling in action (e.g. 'what is 3+3?').  
  Your chat history will be saved in: <local working directory>/tmpq1n1f6qk.json
Chat history file not found. Starting a new conversation.
User:> Hello, how are you?
Mosscap:> Hello! I'm here and ready to help. What do you need today?
Saving 3 messages to the file.
Chat history successfully loaded 3 messages.
User:> exit
"""


async def main() -> None:
    chatting = True
    with tempfile.NamedTemporaryFile(mode="w+", dir=".", suffix=".json", delete=True) as file:
        print(
            "Welcome to the chat bot!\n"
            "  Type 'exit' to exit.\n"
            "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
            f"  Your chat history will be saved in: {file.name}"
        )
        try:
            while chatting:
                chatting = await chat(file.name)
        except Exception:
            print("Closing and removing the file.")


if __name__ == "__main__":
    asyncio.run(main())
