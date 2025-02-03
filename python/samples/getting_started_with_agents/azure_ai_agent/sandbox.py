# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with the
    OpenAPI tool from the Azure Agents service using a synchronous client.
    To learn more about OpenAPI specs, visit https://learn.microsoft.com/openapi

USAGE:
    python sample_agents_openapi.py

    Before running the sample:

    pip install azure-ai-projects azure-identity jsonref

    Set these environment variables with your own values:
    1) PROJECT_CONNECTION_STRING - The project connection string, as found in the overview page of your
       Azure AI Foundry project.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in
       the "Models + endpoints" tab in your Azure AI Foundry project.
"""

import os

import jsonref
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import OpenApiAnonymousAuthDetails, OpenApiTool
from azure.identity import DefaultAzureCredential

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=os.environ["AZURE_AI_AGENT_PROJECT_CONNECTION_STRING"],
)
# [START create_agent_with_openapi]

openapi_spec_file_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "resources",
)

# Create Auth object for the OpenApiTool (note that connection or managed identity auth setup requires additional setup in Azure)
auth = OpenApiAnonymousAuthDetails()

# Initialize agent OpenApi tool using the read in OpenAPI spec

with open(os.path.join(openapi_spec_file_path, "weather.json"), "r") as weather_file:
    weather_openapi_spec = jsonref.loads(weather_file.read())

openapi_weather = OpenApiTool(
    name="get_weather", spec=weather_openapi_spec, description="Retrieve weather information for a location", auth=auth
)

with open(os.path.join(openapi_spec_file_path, "countries.json"), "r") as countries_file:
    countries_openapi_spec = jsonref.loads(countries_file.read())

openapi_countries = OpenApiTool(
    name="get_country", spec=countries_openapi_spec, description="Retrieve country information", auth=auth
)

# Create agent with OpenApi tool and process assistant run
with project_client:
    agent = project_client.agents.create_agent(
        model=os.environ["AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="You are a helpful assistant",
        tools=openapi_weather.definitions,
    )

    # [END create_agent_with_openapi]

    print(f"Created agent, ID: {agent.id}")

    # Create thread for communication
    thread = project_client.agents.create_thread()
    print(f"Created thread, ID: {thread.id}")

    # Create message to thread
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="What is the name and population of the country that uses currency with abbreviation THB?",
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

    # Fetch and log all messages
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")
