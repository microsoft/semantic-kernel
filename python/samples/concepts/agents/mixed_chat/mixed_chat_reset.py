# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import TYPE_CHECKING

from semantic_kernel.agents import AgentGroupChat, AzureAssistantAgent, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureOpenAISettings
from semantic_kernel.contents import AuthorRole
from semantic_kernel.kernel import Kernel

if TYPE_CHECKING:
    pass

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI, a chat completion
agent and have them participate in a group chat to work towards
the user's requirement. It also demonstrates how the underlying
agent reset method is used to clear the current state of the chat

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    # First create the ChatCompletionAgent
    chat_agent = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("chat"),
        name="chat_agent",
        instructions="""
            The user may either provide information or query on information previously provided. 
            If the query does not correspond with information provided, inform the user that their query 
            cannot be answered.
            """,
    )

    # Next, we will create the AzureAssistantAgent

    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        name="copywriter",
        instructions="""
            The user may either provide information or query on information previously provided. 
            If the query does not correspond with information provided, inform the user that their query 
            cannot be answered.
            """,
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    assistant_agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Create the AgentGroupChat object, which will manage the chat between the agents
    # We don't always need to specify the agents in the chat up front
    # As shown below, calling `chat.invoke(agent=<agent>)` will automatically add the
    # agent to the chat
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
