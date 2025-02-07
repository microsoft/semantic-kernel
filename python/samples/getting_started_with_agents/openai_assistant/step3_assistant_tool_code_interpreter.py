# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import AzureAssistantAgent, OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant's code interpreter functionality to have it write       #
# Python code to print Fibonacci numbers.                           #
#####################################################################

# Create the instance of the Kernel
kernel = Kernel()

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = False


async def main():
    # Define a service_id for the sample
    service_id = "agent"
    AGENT_NAME = "CodeRunner"
    AGENT_INSTRUCTIONS = "Run the provided code file and return the result."

    # Create the agent
    if use_azure_openai:
        agent = await AzureAssistantAgent.create(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_code_interpreter=True,
        )
    else:
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel,
            service_id=service_id,
            name=AGENT_NAME,
            instructions=AGENT_INSTRUCTIONS,
            enable_code_interpreter=True,
        )

    thread_id = await agent.create_thread()

    user_input = "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?"
    print(f"# User: '{user_input}'")
    try:
        await agent.add_chat_message(
            thread_id=thread_id,
            message=ChatMessageContent(
                role=AuthorRole.USER,
                content=user_input,
            ),
        )
        async for content in agent.invoke(thread_id=thread_id):
            if content.role != AuthorRole.TOOL:
                print(f"# Agent: {content.content}")
    finally:
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
