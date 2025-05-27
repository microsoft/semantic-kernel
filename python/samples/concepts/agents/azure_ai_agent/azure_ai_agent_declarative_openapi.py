# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions using the OpenAPI tool. The agent is then used to answer user 
questions that leverage a free weather API.
"""

# Toggle between a JSON or a YAML OpenAPI spec
USE_JSON_OPENAPI_SPEC = True

json_openapi_spec = """
type: foundry_agent
name: WeatherAgent
instructions: Answer questions about the weather. For all other questions politely decline to answer.
description: This agent answers question about the weather.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    endpoint: ${AzureAI:Endpoint}
  options:
    temperature: 0.4
tools:
  - type: openapi
    id: GetCurrentWeather
    description: Retrieves current weather data for a location based on wttr.in.
    options:
      specification: |
        {
          "openapi": "3.1.0",
          "info": {
            "title": "Get Weather Data",
            "description": "Retrieves current weather data for a location based on wttr.in.",
            "version": "v1.0.0"
          },
          "servers": [
            {
              "url": "https://wttr.in"
            }
          ],
          "auth": [],
          "paths": {
            "/{location}": {
              "get": {
                "description": "Get weather information for a specific location",
                "operationId": "GetCurrentWeather",
                "parameters": [
                  {
                    "name": "location",
                    "in": "path",
                    "description": "City or location to retrieve the weather for",
                    "required": true,
                    "schema": {
                      "type": "string"
                    }
                  },
                  {
                    "name": "format",
                    "in": "query",
                    "description": "Always use j1 value for this parameter",
                    "required": true,
                    "schema": {
                      "type": "string",
                      "default": "j1"
                    }
                  }
                ],
                "responses": {
                  "200": {
                    "description": "Successful response",
                    "content": {
                      "text/plain": {
                        "schema": {
                          "type": "string"
                        }
                      }
                    }
                  },
                  "404": {
                    "description": "Location not found"
                  }
                },
                "deprecated": false
              }
            }
          },
          "components": {
            "schemes": {}
          }
        }
"""

yaml_openapi_spec = """
type: foundry_agent
name: WeatherAgent
instructions: Answer questions about the weather. For all other questions politely decline to answer.
description: This agent answers question about the weather.
model:
  id: ${AzureAI:ChatModelId}
  options:
    temperature: 0.4
tools:
  - type: openapi
    id: GetCurrentWeather
    description: Retrieves current weather data for a location based on wttr.in.
    options:
      specification:
        openapi: "3.1.0"
        info:
          title: "Get Weather Data"
          description: "Retrieves current weather data for a location based on wttr.in."
          version: "v1.0.0"
        servers:
          - url: "https://wttr.in"
        auth: []
        paths:
          "/{location}":
            get:
              description: "Get weather information for a specific location"
              operationId: "GetCurrentWeather"
              parameters:
                - name: "location"
                  in: "path"
                  description: "City or location to retrieve the weather for"
                  required: true
                  schema:
                    type: "string"
                - name: "format"
                  in: "query"
                  description: "Always use j1 value for this parameter"
                  required: true
                  schema:
                    type: "string"
                    default: "j1"
              responses:
                "200":
                  description: "Successful response"
                  content:
                    text/plain:
                      schema:
                        type: "string"
                "404":
                  description: "Location not found"
              deprecated: false
        components:
          schemes: {}
"""

settings = AzureAIAgentSettings()  # ChatModelId & Endpoint come from .env/env vars


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Create the AzureAI Agent from the YAML spec
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                yaml_str=json_openapi_spec if USE_JSON_OPENAPI_SPEC else yaml_openapi_spec,
                client=client,
                settings=settings,
            )

            # Define the task for the agent
            TASK = "What is the current weather in Seoul?"

            print(f"# User: '{TASK}'")

            # Invoke the agent for the specified task
            async for response in agent.invoke(
                messages=TASK,
            ):
                print(f"# {response.name}: {response}")
        finally:
            # Cleanup: Delete the agent, vector store, and file
            await client.agents.delete_agent(agent.id)

        """
        Sample output:

        # User: 'What is the current weather in Seoul?'
        # WeatherAgent: The current weather in Seoul is 14°C (57°F) with "light drizzle." It feels like 13°C (55°F). 
            The humidity is at 81%, and there is heavy cloud cover (99%). The visibility is reduced to 2 km (1 mile), 
            and the wind is coming from the east at 11 km/h (7 mph)
        """


if __name__ == "__main__":
    asyncio.run(main())
