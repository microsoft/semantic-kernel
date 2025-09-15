# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import Awaitable, Callable

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.filters import FunctionInvocationContext
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions.kernel_arguments import KernelArguments

# This sample shows how to use a filter to use a fallback service if the default service fails to execute the function.
# this works by replacing the settings that point to the default service
# with the settings that point to the fallback service
# after the default service fails to execute the function.

logger = logging.getLogger(__name__)


class RetryFilter:
    """A filter that retries the function invocation with a different model if it fails."""

    def __init__(self, default_service_id: str, fallback_service_id: str):
        """Initialize the filter with the default and fallback service ids."""
        self.default_service_id = default_service_id
        self.fallback_service_id = fallback_service_id

    async def retry_filter(
        self,
        context: FunctionInvocationContext,
        next: Callable[[FunctionInvocationContext], Awaitable[None]],
    ) -> None:
        """A filter that retries the function invocation with a different model if it fails."""
        try:
            # try the default function
            await next(context)
        except Exception as ex:
            print("Expected failure to execute the function: ", ex)
            # if the default function fails, try the fallback function
            if (
                context.arguments
                and context.arguments.execution_settings
                and self.default_service_id in context.arguments.execution_settings
            ):
                # get the settings for the default service
                settings = context.arguments.execution_settings.pop(self.default_service_id)
                settings.service_id = self.fallback_service_id
                # add them back with the right service id
                context.arguments.execution_settings[self.fallback_service_id] = settings
                # try again!
                await next(context)
            else:
                raise ex


async def main() -> None:
    # set the ids for the default and fallback services
    default_service_id = "default_service"
    fallback_service_id = "fallback_service"
    kernel = Kernel()
    # create the filter with the ids
    retry_filter = RetryFilter(default_service_id=default_service_id, fallback_service_id=fallback_service_id)
    # add the filter to the kernel
    kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, retry_filter.retry_filter)

    # add the default and fallback services
    default_service = OpenAIChatCompletion(service_id=default_service_id, api_key="invalid_key")
    kernel.add_service(default_service)
    fallback_service = OpenAIChatCompletion(service_id=fallback_service_id)
    kernel.add_service(fallback_service)

    # create the settings for the request
    request_settings = OpenAIChatPromptExecutionSettings(service_id=default_service_id)
    # invoke a simple prompt function
    response = await kernel.invoke_prompt(
        function_name="retry_function",
        prompt="How are you today?",
        arguments=KernelArguments(settings=request_settings),
    )

    print("Model response: ", response)

    # Sample output:
    # Expected failure to execute the function:  Error occurred while invoking function retry_function:
    # ("<class 'semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.OpenAIChatCompletion'> service
    # failed to complete the prompt", AuthenticationError("Error code: 401 - {'error': {'message': 'Incorrect API key
    # provided: invalid_key. You can find your API key at https://platform.openai.com/account/api-keys.', 'type':
    # 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}"))
    # Model response:  I'm just a program, so I don't experience feelings, but I'm here and ready to help you out.
    # How can I assist you today?


if __name__ == "__main__":
    asyncio.run(main())
