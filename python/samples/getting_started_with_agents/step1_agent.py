# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

###################################################################
# The following sample demonstrates how to create a simple,       #
# non-group agent that repeats the user message in the voice      #
# of a pirate and then ends with a parrot sound.                  #
###################################################################

# To toggle streaming or non-streaming mode, change the following boolean
streaming = True

# Define the agent name and instructions
PARROT_NAME = "Parrot"
PARROT_INSTRUCTIONS = (
    "Repeat the user message in the voice of a pirate and then end with a parrot sound."
)


async def invoke_agent(agent: ChatCompletionAgent, input: str, chat: ChatHistory):
    """Invoke the agent with the user input."""
    chat.add_user_message(input)

    print(f"# {AuthorRole.USER}: '{input}'")

    if streaming:
        contents = []
        content_name = ""
        async for content in agent.invoke_stream(chat):
            content_name = content.name
            contents.append(content)
        streaming_chat_message = reduce(lambda first, second: first + second, contents)
        print(f"# {content.role} - {content_name or '*'}: '{streaming_chat_message}'")
        chat.add_message(content)
    else:
        async for content in agent.invoke(chat):
            print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
            chat.add_message(content)


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Add the OpenAIChatCompletion AI Service to the Kernel
    kernel.add_service(AzureChatCompletion(service_id="agent"))

    # Create the agent
    agent = ChatCompletionAgent(
        service_id="agent",
        kernel=kernel,
        name=PARROT_NAME,
        instructions=PARROT_INSTRUCTIONS,
    )

    # Define the chat history
    chat = ChatHistory()

    # Respond to user input
    await invoke_agent(agent, "Fortune favors the bold.", chat)
    await invoke_agent(agent, "I came, I saw, I conquered.", chat)
    await invoke_agent(agent, "Practice makes perfect.", chat)


if __name__ == "__main__":
    asyncio.run(main())
