# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent

"""
The following sample demonstrates how to use an already existing
Azure AI Agent within Semantic Kernel. This sample requires that you
have an existing agent created either previously in code or via the
Azure Portal (or CLI).
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "Why is the sky blue?",
]


async def main() -> None:
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Retrieve the agent definition based on the `assistant_id`
        # Replace the "your-assistant-id" with the actual assistant ID
        # you want to use.
        agent_definition = await client.agents.get_agent(
            assistant_id="your-assistant-id",
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. Create a new thread on the Azure AI agent service
        thread = await client.agents.create_thread()

        try:
            for user_input in USER_INPUTS:
                # 4. Add the user input as a chat message
                await agent.add_chat_message(thread_id=thread.id, message=user_input)
                print(f"# User: '{user_input}'")
                # 5. Invoke the agent for the specified thread for response
                response = await agent.get_response(thread_id=thread.id)
                print(f"# {response.name}: {response}")
        finally:
            # 6. Cleanup: Delete the thread and agent
            await client.agents.delete_thread(thread.id)
            # Do not clean up the assistant so it can be used again

        """
        Sample Output:
        # User: 'Why is the sky blue?'
        # Agent: The sky appears blue because molecules in the Earth's atmosphere scatter sunlight, 
        and blue light is scattered more than other colors due to its shorter wavelength.
        """


if __name__ == "__main__":
    asyncio.run(main())
