# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

"""
The following sample demonstrates how to create a chat completion agent that
answers user questions using the Azure Chat Completion service. The Chat Completion
Service is first added to the kernel, and the kernel is passed in to the
ChatCompletionAgent constructor. This sample demonstrates the basic steps to
create an agent and simulate a conversation with the agent.

Note: if both a service and a kernel are provided, the service will be used.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history needs to be maintained by the caller in the chat history object.
"""

# Simulate a conversation with the agent
USER_INPUTS = [
    "Hello, I am John Doe.",
    "What is your name?",
    "What is my name?",
]


async def main():
    # 1. Create the instance of the Kernel to register an AI service
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion())

    # 2. Create the agent
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Assistant",
        instructions="Answer the user's questions.",
    )

    # 3. Create a thread to hold the conversation
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ChatHistoryAgentThread = None

    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        # 4. Invoke the agent for a response
        response = await agent.get_response(
            messages=user_input,
            thread=thread,
        )
        print(f"# {response.name}: {response}")
        thread = response.thread

    # 4. Cleanup: Clear the thread
    await thread.delete() if thread else None

    """
    Sample output:
    # User: Hello, I am John Doe.
    # Assistant: Hello, John Doe! How can I assist you today?
    # User: What is your name?
    # Assistant: I don't have a personal name like a human does, but you can call me Assistant.?
    # User: What is my name?
    # Assistant: You mentioned that your name is John Doe. How can I assist you further, John?
    """


if __name__ == "__main__":
    asyncio.run(main())
