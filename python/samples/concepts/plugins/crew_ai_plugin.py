# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.core_plugins.crew_ai import CrewAIEnterprise, InputMetadata
from semantic_kernel.core_plugins.crew_ai.crew_ai_settings import CrewAISettings
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel

logging.basicConfig(level=logging.INFO)


async def using_crew_ai_enterprise():
    settings = CrewAISettings.create()
    crew = CrewAIEnterprise(settings=settings)

    # The required inputs for the Crew must be known in advance. This example is modeled after the
    # Enterprise Content Marketing Crew Template and requires the following inputs:
    inputs = {"company": "CrewAI", "topic": "Agentic products for consumers"}

    # Invoke directly with our inputs
    kickoff_id = await crew.kickoff(inputs)
    print(f"CrewAI Enterprise Crew kicked off with ID: {kickoff_id}")

    # Wait for completion
    result = await crew.wait_for_crew_completion(kickoff_id)
    print("CrewAI Enterprise Crew completed with the following result:")
    print(result)


async def using_crew_ai_enterprise_as_plugin():
    settings = CrewAISettings.create()
    crew = CrewAIEnterprise(settings=settings)

    # Define the description of the Crew. This will used as the semantic description of the plugin.
    crew_description = (
        "Conducts thorough research on the specified company and topic to identify emerging trends,"
        "analyze competitor strategies, and gather data-driven insights."
    )

    # The required inputs for the Crew must be known in advance. This example is modeled after the
    # Enterprise Content Marketing Crew Template and requires string inputs for the company and topic.
    # We need to describe the type and purpose of each input to allow the LLM to invoke the crew as expected.
    crew_plugin_definitions = [
        InputMetadata(name="company", type="string", description="The name of the company that should be researched"),
        InputMetadata(name="topic", type="string", description="The topic that should be researched"),
    ]

    # Create the CrewAI Plugin. This builds a plugin that can be added to the Kernel and invoked like any other plugin.
    # The plugin will contain the following functions:
    # - kickoff: Starts the Crew with the specified inputs and returns the Id of the scheduled kickoff.
    # - kickoff_and_wait: Starts the Crew with the specified inputs and waits for the Crew to complete before returning
    #   the result.
    # - wait_for_completion: Waits for the specified Crew kickoff to complete and returns the result.
    # - get_status: Gets the status of the specified Crew kickoff.
    crew_plugin = crew.create_kernel_plugin(
        name="EnterpriseContentMarketingCrew",
        description=crew_description,
        input_metadata=crew_plugin_definitions,
    )

    # Example of invoking the plugin directly
    kickoff_and_wait_function: KernelFunction = crew_plugin["kickoff_and_wait"]
    result = await kickoff_and_wait_function.invoke(
        kernel=Kernel(), arguments=KernelArguments(company="CrewAI", topic="Consumer AI Products")
    )

    print(result)


if __name__ == "__main__":
    # asyncio.run(using_crew_ai_enterprise())
    asyncio.run(using_crew_ai_enterprise_as_plugin())
