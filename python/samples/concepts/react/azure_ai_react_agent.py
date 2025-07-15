# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
import re
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function, KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig

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
"""

# React prompt template that guides the agent through the reasoning-acting cycle
REACT_PROMPT_TEMPLATE = """
[INSTRUCTION]
Answer the following questions as accurately as possible using the provided functions.

[AVAILABLE FUNCTIONS]
The function definitions below are in the following format:
<functionName>: <description>
 - <parameterName>: <parameterDescription>
 - ...
[END AVAILABLE FUNCTIONS]

[USAGE INSTRUCTIONS]
To use the functions, specify a JSON blob representing an action. The JSON blob should contain the fully qualified name of the function to use, and an "action_variables" key with a JSON object of string values to use when calling the function.
Do not call functions directly; they must be invoked through an action.

Here is an example of a valid $JSON_BLOB:
```
{
  "action": "CalculatorPlugin.Add",
  "action_variables": {"number1": "5", "number2": "3"}
}
```

IMPORTANT: 
* Use only the available functions listed in the [AVAILABLE FUNCTIONS] section.
* Do not attempt to use any other functions that are not specified.
* You must provide a single action per step.
* All parameter values must be strings.
[END USAGE INSTRUCTIONS]
[END INSTRUCTION]

[THOUGHT PROCESS]
[QUESTION]
{{$question}}
[THOUGHT]
To solve this problem, I should carefully analyze the given question and identify the necessary steps. Any facts I discover earlier in my thought process should be repeated here to keep them readily available.
[ACTION]
$JSON_BLOB
[OBSERVATION]
The result of the action will be provided here.
... (These THOUGHT/ACTION/OBSERVATION can repeat until the final answer is reached.)
[FINAL ANSWER]
Once I have gathered all the necessary observations and performed any required actions, provide the final answer in a clear and human-readable format.
[END THOUGHT PROCESS]

IMPORTANT REMINDER: Your response should contain only one next step with a single [ACTION] part. Do not provide more than one step at a time.

Begin!

[AVAILABLE FUNCTIONS]
{{$function_descriptions}}
[END AVAILABLE FUNCTIONS]
[QUESTION]
{{$question}}
{{$agent_scratchpad}}
[THOUGHT]
"""


# Sample plugins for the React agent to use
class CalculatorPlugin:
    """A calculator plugin that provides basic mathematical operations."""

    @kernel_function(description="Adds two numbers together.")
    def add(
        self,
        number1: Annotated[str, "The first number to add"],
        number2: Annotated[str, "The second number to add"],
    ) -> Annotated[str, "The sum of the two numbers"]:
        try:
            result = float(number1) + float(number2)
            return str(result)
        except ValueError:
            return "Error: Invalid number format"

    @kernel_function(description="Multiplies two numbers together.")
    def multiply(
        self,
        number1: Annotated[str, "The first number to multiply"],
        number2: Annotated[str, "The second number to multiply"],
    ) -> Annotated[str, "The product of the two numbers"]:
        try:
            result = float(number1) * float(number2)
            return str(result)
        except ValueError:
            return "Error: Invalid number format"

    @kernel_function(description="Divides the first number by the second number.")
    def divide(
        self,
        number1: Annotated[str, "The dividend"],
        number2: Annotated[str, "The divisor"],
    ) -> Annotated[str, "The quotient of the division"]:
        try:
            num1, num2 = float(number1), float(number2)
            if num2 == 0:
                return "Error: Division by zero"
            result = num1 / num2
            return str(result)
        except ValueError:
            return "Error: Invalid number format"


class WeatherPlugin:
    """A simple weather plugin for demonstration purposes."""

    @kernel_function(description="Gets the current weather for a given city.")
    def get_weather(
        self, city: Annotated[str, "The name of the city"]
    ) -> Annotated[str, "The current weather information"]:
        # Simulated weather data
        weather_data = {
            "istanbul": "Sunny, 22°C",
            "ankara": "Cloudy, 18°C",
            "izmir": "Partly cloudy, 25°C",
            "antalya": "Sunny, 28°C",
            "new york": "Rainy, 15°C",
            "london": "Foggy, 12°C",
            "paris": "Sunny, 20°C",
        }
        city_lower = city.lower()
        if city_lower in weather_data:
            return f"The weather in {city} is: {weather_data[city_lower]}"
        else:
            return f"Weather information for {city} is not available."


def extract_function_descriptions(kernel: Kernel) -> str:
    """Extract function descriptions from kernel plugins for the React prompt."""
    descriptions = []

    for plugin_name, plugin in kernel.plugins.items():
        for function_name, function in plugin.items():
            full_name = f"{plugin_name}.{function_name}"
            desc = function.metadata.description or "No description available"

            descriptions.append(f"{full_name}: {desc}")

            # Add parameter descriptions
            for param in function.metadata.parameters:
                param_desc = param.description or "No description"
                descriptions.append(f" - {param.name}: {param_desc}")

    return "\n".join(descriptions)


def parse_action_from_response(response: str) -> tuple[str | None, dict[str, str]]:
    """Parse the action JSON blob from the agent's response."""
    # Look for JSON blob in the response
    json_pattern = r"```\s*\n?({.*?})\s*\n?```"
    match = re.search(json_pattern, response, re.DOTALL)

    if not match:
        # Try to find JSON without code blocks
        json_pattern = r'({[^}]*"action"[^}]*})'
        match = re.search(json_pattern, response, re.DOTALL)

    if match:
        try:
            action_data = json.loads(match.group(1))
            action_name = action_data.get("action")
            action_variables = action_data.get("action_variables", {})
            return action_name, action_variables
        except json.JSONDecodeError:
            pass

    return None, {}


async def execute_react_step(
    agent: ChatCompletionAgent, question: str, scratchpad: str
) -> tuple[str, bool]:
    """Execute one step of the React cycle and return the updated scratchpad and completion status."""

    # Get function descriptions from the agent's kernel
    function_descriptions = extract_function_descriptions(agent.kernel)

    # Create the full prompt with current scratchpad
    prompt_args = KernelArguments(
        question=question,
        function_descriptions=function_descriptions,
        agent_scratchpad=scratchpad,
    )

    # Get agent's response
    response = await agent.get_response(messages="", arguments=prompt_args)
    response_text = str(response.content)

    print(f"Agent Response:\n{response_text}\n")

    # Check if this is a final answer
    if "[FINAL ANSWER]" in response_text:
        return scratchpad + response_text, True

    # Parse action from response
    action_name, action_variables = parse_action_from_response(response_text)

    if action_name and action_variables:
        # Execute the action
        try:
            # Parse plugin and function names
            parts = action_name.split(".")
            if len(parts) == 2:
                plugin_name, function_name = parts

                if plugin_name in agent.kernel.plugins:
                    function = agent.kernel.plugins[plugin_name][function_name]
                    result = await function.invoke(
                        kernel=agent.kernel, arguments=action_variables
                    )
                    observation = f"[OBSERVATION]\n{result.value}\n"
                else:
                    observation = (
                        f"[OBSERVATION]\nError: Plugin '{plugin_name}' not found.\n"
                    )
            else:
                observation = (
                    f"[OBSERVATION]\nError: Invalid action format '{action_name}'.\n"
                )

        except Exception as e:
            observation = f"[OBSERVATION]\nError executing action: {str(e)}\n"
    else:
        observation = "[OBSERVATION]\nFailed to parse action from response.\n"

    # Update scratchpad with the step
    updated_scratchpad = scratchpad + response_text + "\n" + observation

    return updated_scratchpad, False


async def run_react_agent(
    agent: ChatCompletionAgent, question: str, max_steps: int = 10
) -> str:
    """Run the React agent on a question with a maximum number of steps."""

    print(f"Question: {question}\n")
    print("=" * 50)

    scratchpad = ""

    for step in range(max_steps):
        print(f"Step {step + 1}:")
        print("-" * 20)

        scratchpad, is_complete = await execute_react_step(agent, question, scratchpad)

        if is_complete:
            print("React cycle completed!")
            break

        if step == max_steps - 1:
            print("Maximum steps reached!")

    return scratchpad


async def main():
    # Create kernel and add plugins
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion())
    kernel.add_plugin(CalculatorPlugin(), "CalculatorPlugin")
    kernel.add_plugin(WeatherPlugin(), "WeatherPlugin")

    # Configure the React prompt template
    prompt_config = PromptTemplateConfig(
        template=REACT_PROMPT_TEMPLATE, template_format="semantic-kernel"
    )

    # Create the React agent
    react_agent = ChatCompletionAgent(
        kernel=kernel,
        name="ReactAgent",
        instructions="You are a helpful assistant that uses the React (Reasoning and Acting) pattern to solve problems step by step.",
        prompt_template_config=prompt_config,
    )

    # Test questions for the React agent
    questions = [
        "What is 15 multiplied by 8, and then add 25 to the result?",
        "What's the weather like in Istanbul and how much is 100 divided by 4?",
        "Calculate 20 + 30, then multiply the result by 2, and tell me the weather in Paris",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{'=' * 60}")
        print(f"TEST {i}")
        print(f"{'=' * 60}")

        result = await run_react_agent(react_agent, question)

        print(f"\nFinal Result:\n{result}")
        print(f"\n{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
