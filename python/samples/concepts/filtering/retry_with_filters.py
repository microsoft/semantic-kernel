# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import Awaitable, Callable

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.filters import FunctionInvocationContext
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions import kernel_function

# This sample shows how to use a filter for retrying a function invocation.
# This sample requires the following components:
# - a ChatCompletionService: This component is responsible for generating responses to user messages.
# - a ChatHistory: This component is responsible for keeping track of the chat history.
# - a Kernel: This component is responsible for managing plugins and filters.
# - a mock plugin: This plugin contains a function that simulates a call to an external service.
# - a filter: This filter retries the function invocation if it fails.

logger = logging.getLogger(__name__)

# The maximum number of retries for the filter
MAX_RETRIES = 3


class WeatherPlugin:
    MAX_FAILURES = 2

    def __init__(self):
        self._invocation_count = 0

    @kernel_function(name="GetWeather", description="Get the weather of the day at the current location.")
    def get_weather(self) -> str:
        """Get the weather of the day at the current location.

        Simulates a call to an external service to get the weather.
        This function is designed to fail a certain number of times before succeeding.
        """
        if self._invocation_count < self.MAX_FAILURES:
            self._invocation_count += 1
            print(f"Number of attempts: {self._invocation_count}")
            raise Exception("Failed to get the weather")

        return "Sunny"


async def retry_filter(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """A filter that retries the function invocation if it fails.

    The filter uses a binary exponential backoff strategy to retry the function invocation.
    """
    for i in range(MAX_RETRIES):
        try:
            await next(context)
            return
        except Exception as e:
            logger.warning(f"Failed to execute the function: {e}")
            backoff = 2**i
            logger.info(f"Sleeping for {backoff} seconds before retrying")


async def main() -> None:
    kernel = Kernel()
    # Register the plugin to the kernel
    kernel.add_plugin(WeatherPlugin(), plugin_name="WeatherPlugin")
    # Add the filter to the kernel as a function invocation filter
    # A function invocation filter is called during when the kernel executes a function
    kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, retry_filter)

    chat_history = ChatHistory()
    chat_history.add_user_message("What is the weather today?")

    chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.OPENAI)
    # Need to set the function choice behavior to auto such that the
    # service will automatically invoke the function in the response.
    request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    response = await chat_completion_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
        # Need to pass the kernel to the chat completion service so that it has access to the plugins and filters
        kernel=kernel,
    )

    print(response)

    # Sample output:
    # Number of attempts: 1
    # Failed to execute the function: Failed to get the weather
    # Number of attempts: 2
    # Failed to execute the function: Failed to get the weather
    # The weather today is Sunny


if __name__ == "__main__":
    asyncio.run(main())
