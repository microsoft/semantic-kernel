# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from azure.ai.projects.models import AzureAISearchTool, ConnectionType
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread

logging.basicConfig(level=logging.WARNING)

"""
The following sample demonstrates how to create a simple,
Azure AI agent that uses the Azure AI Search tool and the demo
hotels-sample-index to answer questions about hotels.

This sample requires:
- A "Standard" Agent Setup (choose the Python (Azure SDK) tab):
https://learn.microsoft.com/en-us/azure/ai-services/agents/quickstart
- An Azure AI Search index named 'hotels-sample-index' created in your
Azure AI Search service. You may follow this guide to create the index:
https://learn.microsoft.com/azure/search/search-get-started-portal
- You will need to make sure your Azure AI Agent project is set up with
the required Knowledge Source to be able to use the Azure AI Search tool.
Refer to the following link for information on how to do this:
https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/azure-ai-search

Refer to the README for information about configuring the index to work
with the sample data model in Azure AI Search.
"""

# The name of the Azure AI Search index, rename as needed
AZURE_AI_SEARCH_INDEX_NAME = "hotels-sample-index"


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        conn_list = await client.connections.list()

        ai_search_conn_id = ""
        for conn in conn_list:
            if conn.connection_type == ConnectionType.AZURE_AI_SEARCH and conn.authentication_type == "ApiKey":
                ai_search_conn_id = conn.id
                break

        ai_search = AzureAISearchTool(index_connection_id=ai_search_conn_id, index_name=AZURE_AI_SEARCH_INDEX_NAME)

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            instructions="Answer questions about hotels using your index.",
            tools=ai_search.definitions,
            tool_resources=ai_search.resources,
            headers={"x-ms-enable-preview": "true"},
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread = None

        user_inputs = [
            "Which hotels are available with full-sized kitchens in Nashville, TN?",
            "Fun hotels with free WiFi.",
        ]

        try:
            for user_input in user_inputs:
                print(f"# User: '{user_input}'\n")
                # Invoke the agent for the specified thread
                async for response in agent.invoke(messages=user_input, thread=thread):
                    print(f"# Agent: {response}\n")
                    thread = response.thread
        finally:
            # Cleanup: Delete the thread and agent
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        """
        Sample output:

        # User: 'Which hotels are available with full-sized kitchens in Nashville, TN?'

        # Agent: In Nashville, TN, there are several hotels available that feature full-sized kitchens:

        1. **Extended-Stay Hotel Options**:
        - Many extended-stay hotels offer suites equipped with full-sized kitchens, which include cookware and
        appliances. These hotels are designed for longer stays, making them a great option for those needing more space
        and kitchen facilities【3:0†source】【3:1†source】.

        2. **Amenities Included**:
        - Most of these hotels provide additional amenities like free Wi-Fi, laundry services, fitness centers, and some
        have on-site dining options【3:1†source】【3:2†source】.

        3. **Location**:
        - The extended-stay hotels are often located near downtown Nashville, making it convenient for guests to
        explore the vibrant local music scene while enjoying the comfort of a home-like
        environment【3:0†source】【3:4†source】.

        If you are looking for specific names or more detailed options, I can further assist you with that!

        # User: 'Fun hotels with free WiFi.'

        # Agent: Here are some fun hotels that offer free WiFi:

        1. **Vibrant Downtown Hotel**:
        - Located near the heart of downtown, this hotel offers a warm atmosphere with free WiFi and even provides a
        delightful milk and cookies treat【7:2†source】.

        2. **Extended-Stay Options**:
        - These hotels often feature fun amenities such as a bowling alley, fitness center, and themed rooms. They also
        provide free WiFi and are well-situated near local attractions【7:0†source】【7:1†source】.

        3. **Luxury Hotel**:
        - Ranked highly by Traveler magazine, this 5-star luxury hotel boasts the biggest rooms in the city, free WiFi,
        espresso in the room, and flexible check-in/check-out options【7:1†source】.

        4. **Budget-Friendly Hotels**:
        - Several budget hotels offer free WiFi, breakfast, and shuttle services to nearby attractions and airports
        while still providing a fun stay【7:3†source】.

        These options ensure you stay connected while enjoying your visit! If you need more specific recommendations or
        details, feel free to ask!
        """


if __name__ == "__main__":
    asyncio.run(main())
