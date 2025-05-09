# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.agents.orchestration.concurrent import ConcurrentOrchestration
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion

"""
The following sample demonstrates how to create a concurrent orchestration for
executing multiple agents on the same task in parallel.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a concurrent orchestration with multiple agents, invoking the orchestration, and finally
waiting for the results.
"""


def agents() -> list[Agent]:
    """Return a list of agents that will participate in the concurrent orchestration.

    Feel free to add or remove agents.
    """
    physics_agent = ChatCompletionAgent(
        name="PhysicsExpert",
        description="An expert in physics",
        instructions="You are an expert in physics. You answer questions from a physics perspective.",
        service=OpenAIChatCompletion(),
    )
    chemistry_agent = ChatCompletionAgent(
        name="ChemistryExpert",
        description="An expert in chemistry",
        instructions="You are an expert in chemistry. You answer questions from a chemistry perspective.",
        service=OpenAIChatCompletion(),
    )

    return [physics_agent, chemistry_agent]


async def main():
    """Main function to run the agents."""
    # 1. Create a concurrent orchestration with multiple agents
    concurrent_orchestration = ConcurrentOrchestration(members=agents())

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await concurrent_orchestration.invoke(
        task="What is temperature?",
        runtime=runtime,
    )

    # 4. Wait for the results
    # Note: the order of the results is not guaranteed to be the same
    # as the order of the agents in the orchestration.
    value = await orchestration_result.get(timeout=20)
    for item in value:
        print(f"# {item.name}: {item.content}")

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

    """
    Sample output:
    # PhysicsExpert: Temperature is a physical quantity that represents the average kinetic energy of the particles in
        a substance. It is an indicator of how hot or cold an object is and determines the direction of heat transfer
        between two objects. Heat flows from a region of higher temperature to a region of lower temperature until
        thermal equilibrium is reached.

        In terms of molecular dynamics, at higher temperatures, particles move more vigorously and have higher kinetic
        energy, whereas at lower temperatures, their motion is less energetic. Temperature scales such as Celsius,
        Fahrenheit, and Kelvin are used to quantify temperature. The Kelvin scale is particularly important in
        scientific contexts because it starts at absolute zero—the theoretical point where particle motion would cease
        completely.

        Temperature also affects various physical properties of materials, such as their state (solid, liquid, or gas),
        density, viscosity, and electrical conductivity. It is a crucial parameter in many areas of physics, from
        thermodynamics to statistical mechanics and beyond.
    # ChemistryExpert: Temperature is a fundamental concept in chemistry and physics, representing a measure of the
        average kinetic energy of the particles in a substance. It reflects how hot or cold an object is and determines
        the direction of heat transfer between substances. In more specific terms:

        1. **Kinetic Energy Perspective:** At the molecular level, temperature is linked to the motions of the particles
        comprising a substance. The greater the motion (translational, rotational, vibrational), the higher the
        temperature. For example, in gases, temperature is directly related to the average kinetic energy of the gas
        particles.

        2. **Thermodynamic View:** Temperature is an intensive property and a state function, meaning it doesn't depend
        on the amount of substance present. It is a critical parameter in the laws of thermodynamics, especially in
        determining the spontaneity of processes and the distribution of energy in a system.

        3. **Scales:** Temperature is measured using various scales, including Celsius (°C), Fahrenheit (°F), and
        Kelvin (K). The Kelvin scale is the SI unit for temperature and starts at absolute zero (0 K), the theoretical
        point where all molecular motion ceases.

        4. **Effect on Chemical Reactions:** Temperature affects reaction rates, equilibrium positions, and the
        solubility of substances. Generally, increasing temperature speeds up chemical reactions due to increased
        molecular collisions and energy overcoming activation barriers.

        Understanding temperature is essential in predicting and explaining chemical behavior and interactions in
        reactions, phases changes, and even biological processes.
    """


if __name__ == "__main__":
    asyncio.run(main())
