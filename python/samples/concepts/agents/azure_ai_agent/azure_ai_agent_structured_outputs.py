# Copyright (c) Microsoft. All rights reserved.

import asyncio
from enum import Enum

from azure.ai.projects.models import (
    ResponseFormatJsonSchema,
    ResponseFormatJsonSchemaType,
)
from azure.identity.aio import DefaultAzureCredential
from pydantic import BaseModel

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
)

"""
The following sample demonstrates how to create an Azure AI Agent
and leverage the agent's ability to return structured outputs, 
based on a user-defined Pydantic model.
"""


# Define a Pydantic model that represents the structured output from the agent
class Planets(str, Enum):
    Earth = "Earth"
    Mars = "Mars"
    Jupyter = "Jupyter"


class Planet(BaseModel):
    planet: Planets
    mass: float


async def main():
    ai_agent_settings = AzureAIAgentSettings()
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
            name="Assistant",
            instructions="Extract the information about planets.",
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="planet_mass",
                    description="Extract planet mass.",
                    schema=Planet.model_json_schema(),
                )
            ),
        )

        # Create the AzureAI Agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # Create a new thread for use with the assistant
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread = None

        user_inputs = ["The mass of the Mars is 6.4171E23 kg; the mass of the Earth is 5.972168E24 kg;"]

        try:
            for user_input in user_inputs:
                print(f"# User: '{user_input}'")
                async for response in agent.invoke(messages=user_input, thread=thread):
                    # The response returned is a Pydantic Model, so we can validate it using the
                    # model_validate_json method
                    response_model = Planet.model_validate_json(str(response.content))
                    print(f"# {response.role}: {response_model}")
                    thread = response.thread
        finally:
            await thread.delete() if thread else None
            await client.agents.delete_agent(agent_definition.id)

        """
        Sample Output:

        # User: 'The mass of the Mars is 6.4171E23 kg; the mass of the Earth is 5.972168E24 kg;'
        # AuthorRole.ASSISTANT: planet=<Planets.Earth: 'Earth'> mass=5.972168e+24
        # AuthorRole.ASSISTANT: planet=<Planets.Mars: 'Mars'> mass=6.4171e+23
        """


if __name__ == "__main__":
    asyncio.run(main())
