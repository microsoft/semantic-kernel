# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.core_plugins import MathPlugin
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a React (Reasoning and Acting) agent
using Azure OpenAI within Semantic Kernel. The React pattern enables the agent to
think step by step, take actions using available functions, and observe the results
before making a final decision.

React stands for:
- Reasoning: The agent thinks about the problem and plans the next step
- Acting: The agent executes an action using available functions  
- Observing: The agent examines the results and decides on the next step

This cycle continues until the agent reaches a final answer.

Key Features:
- Uses Semantic Kernel's core MathPlugin instead of custom calculator functions
- Leverages built-in function calling instead of manual execution
- Simplified implementation using agent's native capabilities
- Clean separation of concerns

Note: This implementation demonstrates the React pattern using Semantic Kernel's
native function calling capabilities, eliminating the need for manual step processing.
"""


class WeatherPlugin:
    """A simple weather plugin for demonstration purposes.
    
    Provides simulated weather data for various cities to showcase
    the React agent's ability to use multiple types of functions.
    """

    @kernel_function(description="Gets the current weather for a given city.")
    def get_weather(
        self, city: Annotated[str, "The name of the city"]
    ) -> Annotated[str, "The current weather information"]:
        weather_data = {
            "istanbul": "Sunny, 22°C", "ankara": "Cloudy, 18°C", "izmir": "Partly cloudy, 25°C",
            "antalya": "Sunny, 28°C", "new york": "Rainy, 15°C", "london": "Foggy, 12°C", "paris": "Sunny, 20°C",
        }
        city_lower = city.lower()
        return f"The weather in {city} is: {weather_data.get(city_lower, 'not available')}"


async def run_react_agent(agent: ChatCompletionAgent, question: str) -> str:
    """Run the React agent using built-in function calling.
    
    The agent automatically handles:
    - Function calling when needed
    - Reasoning through the problem
    - Providing final answers
    
    No manual step processing required!
    """
    print(f"Question: {question}\n")
    print("=" * 50)
    
    # Let the agent handle everything automatically
    response = await agent.get_response(messages=question)
    
    print(f"Agent Response: {response.content}")
    return str(response.content)


async def main():
    """Main function demonstrating the simplified React agent implementation.
    
    Uses Semantic Kernel's native function calling capabilities instead of
    manual step processing.
    """
    # Setup kernel and services
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion())
    
    # Add plugins - agent will automatically discover and use them
    kernel.add_plugin(MathPlugin(), "math")
    kernel.add_plugin(WeatherPlugin(), "WeatherPlugin")

    # Create React agent with automatic function calling
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="ReactAgent",
        instructions="""You are a React (Reasoning and Acting) agent that follows a specific thinking pattern.

        React means:
        - **Reasoning**: Think step by step about the problem, analyze what you know and what you need to find out
        - **Acting**: Take actions by calling functions when you need more information or to perform calculations  
        - **Observing**: Analyze the results of your actions and decide what to do next

        For each problem, follow this cycle:

        1. **THOUGHT**: Start by reasoning about the problem
        - What is being asked?
        - What information do I already have?
        - What do I need to find out or calculate?
        - What's my plan to solve this?

        2. **ACTION**: If you need to take an action (call a function), do it
        - Only call functions when necessary
        - Use the most appropriate function for the task

        3. **OBSERVATION**: After each action, reflect on the results
        - What did I learn from this action?
        - Does this help answer the original question?
        - Do I need to take more actions, or can I provide the final answer?

        4. **REPEAT**: Continue the Thought-Action-Observation cycle until you can provide a complete answer

        Always show your reasoning process clearly. Think out loud so users can follow your logic.""",
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    # Test questions demonstrating automatic function calling
    questions = [
        "What is 15 multiplied by 8, and then add 25 to the result?",
        "What's the weather like in Istanbul and how much is 100 divided by 4?", 
        "Calculate 20 + 30, then multiply the result by 2, and tell me the weather in Paris",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST {i}")
        print(f"{'=' * 60}")

        result = await run_react_agent(agent, question)
        print(f"\nResult: {result}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
