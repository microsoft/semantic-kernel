# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.ai.projects.models import TruncationObject
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    AzureAIAgentThread,
)

"""
The following sample demonstrates how to create an Azure AI Agent Agent
and configure a truncation strategy for the agent.
"""

USER_INPUTS = [
    "Why is the sky blue?",
    "What is the speed of light?",
    "What have we been talking about?",
]


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        # Create the agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="TruncateAgent",
            instructions="You are a helpful assistant that answers user questions in one sentence.",
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        thread: AzureAIAgentThread | None = None

        # Options are "auto" or "last_messages"
        # If using "last_messages", specify the number of messages to keep with `last_messages` kwarg
        truncation_strategy = TruncationObject(type="last_messages", last_messages=2)

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. Invoke the agent with the specified message for response
                response = await agent.get_response(
                    messages=user_input, thread=thread, truncation_strategy=truncation_strategy
                )
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            # 6. Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

    """
    Sample Output:

    # User: Why is the sky blue?
    # TruncateAgent: The sky appears blue because molecules in the Earth's atmosphere scatter sunlight in all 
        directions, and blue light is scattered more than other colors due to its shorter wavelength.
    # User: What is the speed of light?
    # TruncateAgent: The speed of light in a vacuum is approximately 299,792,458 meters per second 
        (or about 186,282 miles per second).
    # User: What have we been talking about?
    # TruncateAgent: I'm sorry, but I don't have access to previous interactions. Could you remind me what 
        we've been discussing?
    """


if __name__ == "__main__":
    asyncio.run(main())
