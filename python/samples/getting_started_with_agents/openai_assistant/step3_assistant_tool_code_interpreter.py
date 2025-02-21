# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole

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
    # Create the OpenAI Assistant Agent
    # client = OpenAIAssistantAgent.create_openai_client()

    # To create an OpenAIAssistantAgent for Azure OpenAI, use the following:
    client = OpenAIAssistantAgent.create_azure_openai_client()

    code_interpreter_tool, code_interpreter_tool_resources = OpenAIAssistantAgent.configure_code_interpreter_tool()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model="gpt-4o",
        name="CodeRunner",
        instructions="Run the provided code file and return the result.",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_tool_resources,
    )

    # Create the OpenAIAssistantAgent instance
    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    user_input = "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101?"
    print(f"# User: '{user_input}'")
    try:
        await agent.add_chat_message(
            thread_id=thread.id,
            message=user_input,
        )
        async for content in agent.invoke(thread_id=thread.id):
            if content.role != AuthorRole.TOOL:
                print(f"# Agent: {content.content}")
    finally:
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
