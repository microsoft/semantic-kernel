# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions. This sample demonstrates the basic steps to create an agent
and simulate a conversation with the agent.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "Hello, I am John Doe.",
    "What is your name?",
    "What is my name?",
]


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Assistant",
            instructions="Answer the user's questions.",
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. Invoke the agent with the specified message for response
                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            # 6. Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        # User: Hello, I am John Doe.
        # Assistant: Hello, John! How can I assist you today?
        # User: What is your name?
        # Assistant: I'm here as your assistant, so you can just call me Assistant. How can I help you today?
        # User: What is my name?
        # Assistant: Your name is John Doe. How can I assist you today, John?
        """


if __name__ == "__main__":
    asyncio.run(main())
