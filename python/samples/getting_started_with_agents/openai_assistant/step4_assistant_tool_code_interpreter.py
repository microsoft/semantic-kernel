# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI and leverage the
assistant's code interpreter functionality to have it write
Python code to print Fibonacci numbers.
"""

TASK = "Use code to determine the values in the Fibonacci sequence that that are less than the value of 101?"


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # 2. Configure the code interpreter tool and resources for the Assistant
    code_interpreter_tool, code_interpreter_tool_resources = AzureAssistantAgent.configure_code_interpreter_tool()

    # 3. Create the assistant on the Azure OpenAI service
    definition = await client.beta.assistants.create(
        model=model,
        name="CodeRunner",
        instructions="Run the provided request as code and return the result.",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_tool_resources,
    )

    # 4. Create a Semantic Kernel agent for the Azure OpenAI assistant
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # 5. Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    print(f"# User: '{TASK}'")
    try:
        # 6. Invoke the agent for the current thread and print the response
        async for response in agent.invoke(messages=TASK, thread=thread):
            print(f"# Agent: {response}")
            thread = response.thread
    finally:
        # 7. Clean up the resources
        await thread.delete() if thread else None
        await agent.client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
