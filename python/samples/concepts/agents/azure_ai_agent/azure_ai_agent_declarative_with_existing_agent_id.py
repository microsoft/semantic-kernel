# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent

"""
The following sample demonstrates how to create an Azure AI agent based 
on an existing agent ID.
"""

# Define the YAML string for the sample
spec = """
id: ${AzureAI:AgentId}
type: foundry_agent
instructions: You are helpful agent who always responds in French.
"""


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Create the AzureAI Agent from the YAML spec
            # Note: the extras can be provided in the short-format (shown below) or
            # in the long-format (as shown in the YAML spec, with the `AzureAI:` prefix).
            # The short-format is used here for brevity
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                yaml_str=spec,
                client=client,
                extras={"AgentId": "<my-agent-id>"},  # Specify the existing agent ID
            )

            # Define the task for the agent
            TASK = "Why is the sky blue?"

            print(f"# User: '{TASK}'")

            # Invoke the agent for the specified task
            async for response in agent.invoke(
                messages=TASK,
            ):
                print(f"# {response.name}: {response}")
        finally:
            # Cleanup: Delete the thread and agent
            await client.agents.delete_agent(agent.id)

        """
        Sample output:

        # User: 'Why is the sky blue?'
        # WeatherAgent: Le ciel est bleu à cause d'un phénomène appelé **diffusion de Rayleigh**. La lumière du 
        Soleil est composée de toutes les couleurs du spectre visible, mais lorsqu'elle traverse l'atmosphère 
        terrestre, elle entre en contact avec les molécules d'air et les particules présentes.

        Les couleurs à courtes longueurs d'onde, comme le bleu et le violet, sont diffusées dans toutes les directions 
        beaucoup plus efficacement que les couleurs à longues longueurs d'onde, comme le rouge et l'orange. Bien que le 
        violet ait une longueur d'onde encore plus courte que le bleu, nos yeux sont moins sensibles à cette couleur, 
        et une partie du violet est également absorbée par la haute atmosphère. Ainsi, le bleu domine, donnant au ciel 
        sa couleur caractéristique.
        """


if __name__ == "__main__":
    asyncio.run(main())
