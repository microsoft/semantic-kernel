# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import os

from azure.ai.projects.models import OpenApiAnonymousAuthDetails, OpenApiTool
from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.contents import AuthorRole

"""
The following sample demonstrates how to create a simple, Azure AI agent that
uses OpenAPI tools to answer user questions.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "What is the name and population of the country that uses currency with abbreviation THB",
    "What is the current weather in the capital city of the country?",
]


async def main() -> None:
    ai_agent_settings = AzureAIAgentSettings()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Read in the OpenAPI spec files
        openapi_spec_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "resources",
        )
        with open(os.path.join(openapi_spec_file_path, "weather.json")) as weather_file:
            weather_openapi_spec = json.loads(weather_file.read())
        with open(os.path.join(openapi_spec_file_path, "countries.json")) as countries_file:
            countries_openapi_spec = json.loads(countries_file.read())

        # 2. Create OpenAPI tools
        # Note that connection or managed identity auth setup requires additional setup in Azure
        auth = OpenApiAnonymousAuthDetails()
        openapi_weather = OpenApiTool(
            name="get_weather",
            spec=weather_openapi_spec,
            description="Retrieve weather information for a location",
            auth=auth,
        )
        openapi_countries = OpenApiTool(
            name="get_country",
            spec=countries_openapi_spec,
            description="Retrieve country information",
            auth=auth,
        )

        # 3. Create an agent on the Azure AI agent service with the OpenAPI tools
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            tools=openapi_weather.definitions + openapi_countries.definitions,
        )

        # 4. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 5. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: '{user_input}'")
                # 7. Invoke the agent for the specified thread for response
                async for response in agent.invoke(messages=user_input, thread=thread):
                    if response.role != AuthorRole.TOOL:
                        print(f"# Agent: {response}")
                    thread = response.thread
        finally:
            # 8. Cleanup: Delete the thread and agent
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        # User: 'What is the name and population of the country that uses currency with abbreviation THB'
        # Agent: It seems I encountered an issue while trying to retrieve data about the country that uses the ...
        
        As of the latest estimates, the population of Thailand is approximately 69 million people. If you ...
        # User: 'What is the current weather in the capital city of the country?'
        # Agent: The current weather in Bangkok, Thailand, the capital city, is as follows:
        
        - **Temperature**: 24°C (76°F)
        - **Feels Like**: 26°C (79°F)
        - **Weather Description**: Light rain
        - **Humidity**: 69%
        - **Cloud Cover**: 75%
        - **Pressure**: 1017 hPa
        - **Wind Speed**: 8 km/h (5 mph) from the east-northeast (ENE)
        - **Visibility**: 10 km (approximately 6 miles)
        
        This weather information reflects the current conditions as of the latest observation. If you need ...
        """


if __name__ == "__main__":
    asyncio.run(main())
