# Copyright (c) Microsoft. All rights reserved.

import asyncio

from foundry_local import FoundryLocalManager
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory

"""
This samples demonstrates how to use the Foundry Local model with the OpenAIChatCompletion service.
The Foundry Local model is a local model that can be used to run the OpenAIChatCompletion service.
To use this sample, you need to install the Foundry Local SDK and service.
For the service refer to this guide: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started
To install the SDK, run the following command:
`pip install foundry-local-sdk`
"""

# The way Foundry Local works, is that it picks the right variant of a model based on the
# hardware available on the machine. For example, if you have a GPU, it will pick the GPU variant
# of the model. If you have a CPU, it will pick the CPU variant of the model.
# The model alias is the name of the model that you want to use.
model_alias = "phi-4-mini"
manager = FoundryLocalManager(model_alias)
# next, download the model to the machine
manager.download_model(model_alias)
# load the model into memory
manager.load_model(model_alias)

service = OpenAIChatCompletion(
    ai_model_id=manager.get_model_info(model_alias).id,
    async_client=AsyncOpenAI(
        base_url=manager.endpoint,
        api_key=manager.api_key,
    ),
)
# if needed, set the other parameters for the execution
request_settings = OpenAIChatPromptExecutionSettings()
# This is the system message that gives the chatbot its personality.
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. Use the tools you have available!
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
    response = await service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
    )
    if response:
        print(f"Mosscap:> {response}")

        # Add the chat message to the chat history to keep track of the conversation.
        chat_history.add_message(response)

    return True


async def main() -> None:
    # Start the chat loop. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()


"""
Sample output:
User:> Why is the sky blue in one sentence?
Mosscap:> The sky appears blue due to Rayleigh scattering, where shorter blue wavelengths of sunlight are scattered in 
    all directions by the gases and particles in Earth's atmosphere more than other colors.
"""


if __name__ == "__main__":
    asyncio.run(main())
