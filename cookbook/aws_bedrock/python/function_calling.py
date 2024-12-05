"""Function calling example using AWS Bedrock with Semantic Kernel.

This example demonstrates how to:
1. Create and register native functions as plugins
2. Use function calling with AWS Bedrock
3. Create semantic functions that orchestrate native functions
4. Handle function execution and errors

The example uses a weather plugin as a demonstration, but the pattern
can be applied to any type of function or API call.

Requirements:
    - AWS credentials configured
    - Access to AWS Bedrock service
    - Required packages: semantic-kernel, boto3

Example usage:
    python function_calling.py
"""

import logging
import random
import sys
from typing import Optional

import semantic_kernel as sk
from semantic_kernel.connectors.ai.bedrock import BedrockChatCompletion
from semantic_kernel.connectors.ai.bedrock.bedrock_config import BedrockConfig
from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelArguments
from semantic_kernel.exceptions import ServiceInitializationError

from config import BEDROCK_SETTINGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherPlugin:
    """Example plugin that simulates weather information retrieval.

    In a real application, this would make API calls to a weather service.
    This example shows how to structure a plugin and use function decorators.
    """

    @kernel_function(
        description="Get the current weather for a specific city",
        name="get_weather"
    )
    def get_weather(self, city: str) -> str:
        """Get current weather information for a city.

        Args:
            city: Name of the city to get weather for

        Returns:
            str: Weather description including temperature and conditions

        Note:
            This is a mock implementation. In a real application,
            you would call a weather API here.
        """
        try:
            # Simulate API call
            temperature = random.randint(0, 35)
            conditions = ["sunny", "cloudy", "rainy", "windy"]
            condition = random.choice(conditions)

            return f"The weather in {city} is {condition} with a temperature of {temperature}°C"

        except Exception as e:
            logger.error(f"Error getting weather for {city}: {str(e)}")
            return f"Sorry, I couldn't get the weather information for {city}"

async def initialize_kernel() -> Optional[sk.Kernel]:
    """Initialize Semantic Kernel with AWS Bedrock.

    Returns:
        sk.Kernel: Initialized kernel with Bedrock chat service
        None: If initialization fails
    """
    try:
        kernel = sk.Kernel()

        # Configure Bedrock service
        config = BedrockConfig(
            model_id=BEDROCK_SETTINGS["model_id"],
            region=BEDROCK_SETTINGS["region"]
        )
        chat_service = BedrockChatCompletion(config)
        kernel.add_chat_service("bedrock", chat_service)

        # Register the weather plugin
        plugins = kernel.import_plugin_from_object(
            WeatherPlugin(),
            plugin_name="Weather"
        )

        logger.info(f"Initialized kernel with Bedrock model: {config.model_id}")
        logger.info("Registered Weather plugin successfully")
        return kernel

    except ServiceInitializationError as e:
        logger.error(f"Failed to initialize Bedrock service: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {str(e)}")
        return None

async def create_weather_assistant(kernel: sk.Kernel) -> Optional[sk.KernelFunction]:
    """Create a semantic function that uses the weather plugin.

    Args:
        kernel: Initialized Semantic Kernel instance

    Returns:
        KernelFunction: The created semantic function
        None: If creation fails
    """
    try:
        prompt = """
        Use the available functions to help the user with weather information.
        If you need weather data, use the Weather.get_weather function.
        Be concise in your responses and consider the context of the question.
        If the user asks about bringing items (umbrella, sunglasses, etc.),
        make a recommendation based on the weather conditions.

        Question: {{$input}}
        """

        return kernel.create_function_from_prompt(
            prompt,
            function_name="weather_assistant",
            description="Assistant that helps with weather information"
        )

    except Exception as e:
        logger.error(f"Failed to create weather assistant: {str(e)}")
        return None

async def process_weather_queries(
    kernel: sk.Kernel,
    weather_assistant: sk.KernelFunction,
    queries: list[str]
):
    """Process a list of weather-related queries.

    Args:
        kernel: Initialized Semantic Kernel instance
        weather_assistant: The weather assistant semantic function
        queries: List of queries to process
    """
    for query in queries:
        print(f"\nUser: {query}")
        try:
            result = await kernel.invoke(
                weather_assistant,
                KernelArguments(input=query)
            )
            print(f"Assistant: {str(result)}\n")

        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            print("Sorry, I couldn't process your weather query. Please try again.")

async def main():
    """Main entry point for the weather assistant application."""
    try:
        # Initialize the kernel
        kernel = await initialize_kernel()
        if not kernel:
            logger.error("Failed to initialize the kernel. Exiting...")
            sys.exit(1)

        # Create the weather assistant
        weather_assistant = await create_weather_assistant(kernel)
        if not weather_assistant:
            logger.error("Failed to create weather assistant. Exiting...")
            sys.exit(1)

        print("\nRunning function calling example with AWS Bedrock...\n")

        # Example queries demonstrating different scenarios
        queries = [
            "What's the weather like in Seattle?",
            "Should I bring an umbrella in New York today?",
            "Is it a good day for a picnic in San Francisco?",
            "What should I wear in London today?"
        ]

        await process_weather_queries(kernel, weather_assistant, queries)

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())