# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with the
    Azure AI Search tool from the Azure Agents service using a synchronous client.
    To learn how to set up an Azure AI Search resource,
    visit https://learn.microsoft.com/azure/search/search-get-started-portal

USAGE:
    python sample_agents_azure_ai_search.py

    Before running the sample:

    pip install azure-ai-projects azure-identity

    Set these environment variables with your own values:
    1) PROJECT_CONNECTION_STRING - The project connection string, as found in the overview page of your
       Azure AI Foundry project.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in
       the "Models + endpoints" tab in your Azure AI Foundry project.
"""


# logging.basicConfig(level=logging.DEBUG)

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AzureAISearchTool, ConnectionType
from azure.identity import DefaultAzureCredential

from semantic_kernel.agents.azure_ai.azure_ai_agent_settings import AzureAIAgentSettings

ai_agent_settings = AzureAIAgentSettings.create()

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
)

# [START create_agent_with_azure_ai_search_tool]
conn_list = project_client.connections.list()
conn_id = ""
for conn in conn_list:
    if conn.connection_type == ConnectionType.AZURE_AI_SEARCH:
        conn_id = conn.id
        break

print(conn_id)

# Initialize agent AI search tool and add the search index connection id
ai_search = AzureAISearchTool(index_connection_id=conn_id, index_name="hotels-sample-index-4")

# Create agent with AI search tool and process assistant run
with project_client:
    agent = project_client.agents.create_agent(
        model=ai_agent_settings.model_deployment_name,
        name="my-assistant",
        instructions="You are a helpful assistant",
        tools=ai_search.definitions,
        tool_resources=ai_search.resources,
        headers={"x-ms-enable-preview": "true"},
    )
    # [END create_agent_with_azure_ai_search_tool]
    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Using the index, which hotels are available with full-sized kitchens in Nashville, TN?",
    )
    print(f"Created message, ID: {message.id}")

    # Create and process agent run in thread with tools
    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        print(f"Run failed: {run.last_error}")

    # Delete the assistant when done
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    run_steps = project_client.agents.list_run_steps(thread_id=thread.id, run_id=run.id)
    print(f"Run steps: {run_steps}")

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
