# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import TYPE_CHECKING

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    pass

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat to work towards
the user's requirement. It also demonstrates how the underlying
agent reset method is used to clear the current state of the chat
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIAssistantAgent.setup_resources()

    # If desired, create using OpenAI resources
    # client, model = OpenAIAssistantAgent.setup_resources()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="copywriter",
        instructions="""
            The user may either provide information or query on information previously provided. 
            If the query does not correspond with information provided, inform the user that their query 
            cannot be answered.
            """,
    )

    # Create the OpenAIAssistantAgent instance
    assistant_agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    chat_agent = ChatCompletionAgent(
        service_id="chat",
        kernel=_create_kernel_with_chat_completion("chat"),
        name="chat_agent",
        instructions="""
            The user may either provide information or query on information previously provided. 
            If the query does not correspond with information provided, inform the user that their query 
            cannot be answered.
            """,
    )

    chat = AgentGroupChat()

    try:
        user_inputs = [
            "What is my favorite color?",
            "I like green.",
            "What is my favorite color?",
            "[RESET]",
            "What is my favorite color?",
        ]

        for user_input in user_inputs:
            # Check for reset indicator
            if user_input == "[RESET]":
                print("\nResetting chat...")
                await chat.reset()
                continue

            # First agent (assistant_agent) receives the user input
            await chat.add_chat_message(user_input)
            print(f"\n{AuthorRole.USER}: '{user_input}'")
            async for message in chat.invoke(agent=assistant_agent):
                if message.content is not None:
                    print(f"\n# {message.role} - {message.name or '*'}: '{message.content}'")

            # Second agent (chat_agent) just responds without new user input
            async for message in chat.invoke(agent=chat_agent):
                if message.content is not None:
                    print(f"\n# {message.role} - {message.name or '*'}: '{message.content}'")
    finally:
        await chat.reset()
        await assistant_agent.client.beta.assistants.delete(assistant_agent.id)


if __name__ == "__main__":
    asyncio.run(main())
