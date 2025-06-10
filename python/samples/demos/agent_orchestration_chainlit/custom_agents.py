# Copyright (c) Microsoft. All rights reserved.

import os

from azure.ai.agents.models import BingGroundingTool
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Load environment variables from .env file
load_dotenv()
# Read the Bing connection name from the loaded environment variables
BING_CONNECTION_NAME = os.getenv("BING_CONNECTION_NAME", "<your-bing-grounding-connection-name>")


class AgentFactory:
    """A collection of custom agents."""

    def __init__(self):
        """Initialize the AgentFactory with Azure credentials and client."""
        self._azure_credential = DefaultAzureCredential()
        self._azure_ai_agent_client = AzureAIAgent.create_client(credential=self._azure_credential)

        self._agents = []

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self._delete_agents()

        if self._azure_credential:
            await self._azure_credential.close()

        if self._azure_ai_agent_client:
            await self._azure_ai_agent_client.close()

    async def _delete_agents(self) -> None:
        """Delete all agents created by this factory."""
        for agent in self._agents:
            if isinstance(agent, AzureAIAgent):
                try:
                    await agent.client.agents.delete_agent(agent.definition.id)
                except Exception as e:
                    print(f"Failed to delete agent {agent.definition.name}: {e}")

    async def create_azure_ai_search_agent(self) -> AzureAIAgent:
        """Create an AzureAIAgent with Bing grounding."""
        bing_connection = await self._azure_ai_agent_client.connections.get(name=BING_CONNECTION_NAME)
        bing_grounding = BingGroundingTool(connection_id=bing_connection.id)

        agent_definition = await self._azure_ai_agent_client.agents.create_agent(
            name="BingGroundingAgent",
            instructions="Perform web search based on the request.",
            description="This agent performs web searches.",
            model=AzureAIAgentSettings().model_deployment_name,
            tools=bing_grounding.definitions,
        )

        agent = AzureAIAgent(
            client=self._azure_ai_agent_client,
            definition=agent_definition,
        )
        self._agents.append(agent)

        return agent
