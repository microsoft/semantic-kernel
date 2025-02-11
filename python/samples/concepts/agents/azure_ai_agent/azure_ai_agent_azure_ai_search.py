# Copyright (c) Microsoft. All rights reserved.

import asyncio

###########################################################################
# The following sample demonstrates how to create a simple,               #
# Azure AI agent that uses the Azure AI Search tool and the demo          #
# hotels-sample-index to answer questions about hotels.                   #
#                                                                         #
# This sample requires:                                                   #
# - A "Standard" Agent Setup (choose the Python (Azure SDK) tab):         #
# https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart   #
# - An Azure AI Search index named 'hotels-sample-index' created in your  #
# Azure AI Search service. You may follow this guide to create the index: #
# https://learn.microsoft.com/azure/search/search-get-started-portal      #
###########################################################################
import logging

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool, ConnectionType
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        conn_list = await client.connections.list()

        ai_search_conn_id = ""
        for conn in conn_list:
            if conn.connection_type == ConnectionType.AZURE_AI_SEARCH:
                ai_search_conn_id = conn.id
                break

        ai_search = AzureAISearchTool(index_connection_id=ai_search_conn_id, index_name="hotels-sample-index")

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            instructions="Answer questions about hotels.",
            tools=ai_search.definitions,
            tool_resources=ai_search.resources,
            headers={"x-ms-enable-preview": "true"},
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a new thread
        thread = await client.agents.create_thread()

        user_inputs = [
            "Which hotels are available with full-sized kitchens in Nashville, TN?",
        ]

        try:
            for user_input in user_inputs:
                # Add the user input as a chat message
                await agent.add_chat_message(
                    thread_id=thread.id,
                    message=ChatMessageContent(role=AuthorRole.USER, content=user_input),
                )
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified thread
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
                        if len(content.items) > 0:
                            for item in content.items:
                                if isinstance(item, AnnotationContent):
                                    print(f"\n`{item.quote}`")
        finally:
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
