# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.projects.models import CodeInterpreterTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create a simple, Azure AI agent that
uses the code interpreter tool to answer a coding question.
"""

TASK = "Use code to determine the values in the Fibonacci sequence that that are less then the value of 101."


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent with a code interpreter on the Azure AI agent service
        code_interpreter = CodeInterpreterTool()
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources,
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. Create a new thread on the Azure AI agent service
        thread = await client.agents.create_thread()

        try:
            # 4. Add the task as a chat message
            await agent.add_chat_message(thread_id=thread.id, message=TASK)
            print(f"# User: '{TASK}'")
            # 5. Invoke the agent for the specified thread for response
            async for content in agent.invoke(thread_id=thread.id):
                if content.role != AuthorRole.TOOL:
                    print(f"# Agent: {content.content}")
        finally:
            # 6. Cleanup: Delete the thread and agent
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        # User: 'Use code to determine the values in the Fibonacci sequence that that are less then the value of 101.'
        # Agent: # Function to generate Fibonacci sequence values less than a given limit
        def fibonacci_less_than(limit):
            fib_sequence = []
            a, b = 0, 1
            while a < limit:
                fib_sequence.append(a)
                a, b = b, a + b
            a, b = 0, 1
            while a < limit:
                fib_sequence.append(a)
            a, b = 0, 1
            while a < limit:
            a, b = 0, 1
            a, b = 0, 1
            while a < limit:
                fib_sequence.append(a)
                a, b = b, a + b
            return fib_sequence
        
        Generate Fibonacci sequence values less than 101
        fibonacci_values = fibonacci_less_than(101)
        fibonacci_values
        # Agent: The values in the Fibonacci sequence that are less than 101 are:
        
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        """


if __name__ == "__main__":
    asyncio.run(main())
