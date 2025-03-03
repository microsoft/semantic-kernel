# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings

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
    ai_agent_settings = AzureAIAgentSettings.create()

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
            # Optionally configure polling options
            # polling_options=RunPollingOptions(run_polling_interval=timedelta(seconds=1)),
        )

        # 3. Create a new thread on the Azure AI agent service
        thread = await client.agents.create_thread()

        try:
            for user_input in USER_INPUTS:
                # 4. Add the user input as a chat message
                await agent.add_chat_message(thread_id=thread.id, message=user_input)
                print(f"# User: {user_input}")
                # 5. Invoke the agent for the specified thread for response
                response = await agent.get_response(thread_id=thread.id)
                print(f"# {response.name}: {response}")
        finally:
            # 6. Cleanup: Delete the thread and agent
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        # User: Hello, I am John Doe.
        # Assistant: Hello, John! How can I assist you today?
        # User: What is your name?
        # Assistant: I’m here as your assistant, so you can just call me Assistant. How can I help you today?
        # User: What is my name?
        # Assistant: Your name is John Doe. How can I assist you today, John?
        """


if __name__ == "__main__":
    asyncio.run(main())
