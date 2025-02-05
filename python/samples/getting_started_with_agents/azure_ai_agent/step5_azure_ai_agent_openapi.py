# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    OpenApiAnonymousAuthDetails,
    OpenApiTool,
)
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

###################################################################
# The following sample demonstrates how to create a simple,       #
# Azure AI agent that uses the code interpreter tool to answer    #
# a coding question.                                              #
###################################################################


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AIProjectClient.from_connection_string(
            credential=creds,
            conn_str=ai_agent_settings.project_connection_string.get_secret_value(),
        ) as client,
    ):
        openapi_spec_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "resources",
        )

        # Create Auth object for the OpenApiTool (note that connection or managed identity
        # auth setup requires additional setup in Azure)
        auth = OpenApiAnonymousAuthDetails()

        # Initialize agent OpenApi tool using the read in OpenAPI spec

        with open(os.path.join(openapi_spec_file_path, "weather.json")) as weather_file:
            weather_openapi_spec = json.loads(weather_file.read())

        openapi_weather = OpenApiTool(
            name="get_weather",
            spec=weather_openapi_spec,
            description="Retrieve weather information for a location",
            auth=auth,
        )

        with open(os.path.join(openapi_spec_file_path, "countries.json")) as countries_file:
            countries_openapi_spec = json.loads(countries_file.read())

        openapi_countries = OpenApiTool(
            name="get_country", spec=countries_openapi_spec, description="Retrieve country information", auth=auth
        )

        # Create agent definition
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=openapi_weather.definitions + openapi_countries.definitions,
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a new thread
        thread = await client.agents.create_thread()

        user_inputs = [
            "What is the name and population of the country that uses currency with abbreviation THB",
            "What is the capital city of the country?",
        ]

        try:
            for user_input in user_inputs:
                # Add the user input as a chat message
                await agent.add_chat_message(
                    thread_id=thread.id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
                )
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified thread
                async for content in agent.invoke(thread_id=thread.id):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
        finally:
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
