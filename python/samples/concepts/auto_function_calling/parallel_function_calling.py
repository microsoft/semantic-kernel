# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
import time
from typing import Annotated

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

# This sample demonstrates how the kernel will execute functions in parallel.
# The output of this sample should look similar to the following:
#
# [2024-09-11 10:15:35.070 INFO] processing 2 tool calls in parallel.
# The employee with ID 123 is named John Doe and they are 30 years old.
# Time elapsed: 11.96s
#
# The mock plugin simulates a long-running operation to fetch the employee's name and age.
# When you run the sample, you should see the total execution time is less than the sum
# of the two function calls because the kernel executes the functions in parallel.

# This concept example shows how to handle both streaming and non-streaming responses
# To toggle the behavior, set the following flag accordingly:
stream = True


def set_up_logging():
    """Set up logging to verify the kernel execute the functions in parallel"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s.%(msecs)03d %(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"),
    )
    # Print only the logs from the chat completion client to reduce the output of the sample
    handler.addFilter(lambda record: record.name == "semantic_kernel.connectors.ai.chat_completion_client_base")

    root_logger.addHandler(handler)


class EmployeePlugin:
    """A mock plugin to simulate a plugin that fetches employee information"""

    @kernel_function(name="get_name", description="Find the name of the employee by the id")
    async def get_name(
        self, id: Annotated[str, "The ID of the employee"]
    ) -> Annotated[str, "The name of the employee"]:
        # Simulate a long-running operation
        await asyncio.sleep(10)
        return "John Doe"

    @kernel_function(name="get_age", description="Get the age of the employee by the id")
    async def get_age(self, id: Annotated[str, "The ID of the employee"]) -> Annotated[int, "The age of the employee"]:
        # Simulate a long-running operation
        await asyncio.sleep(10)
        return 30


async def main():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id="open_ai"))
    kernel.add_plugin(EmployeePlugin(), "EmployeePlugin")

    # With this query, the model will call the get_name and get_age functions in parallel.
    # Note that for certain queries, the model may choose to call the functions sequentially.
    # For example, if the available functions are `get_email_by_id` and `get_name_by_email`,
    # the model will not be able to call them in parallel because the second function depends
    # on the result of the first function.
    query = "What is the name and age of the employee of ID 123?"
    arguments = KernelArguments(
        settings=PromptExecutionSettings(
            # Set the function_choice_behavior to auto to let the model
            # decide which function to use, and let the kernel automatically
            # execute the functions.
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )
    )

    start = time.perf_counter()

    if stream:
        async for result in kernel.invoke_prompt_stream(query, arguments=arguments):
            print(str(result[0]), end="")
        print()
    else:
        result = await kernel.invoke_prompt(query, arguments=arguments)
        print(result)

    print(f"Time elapsed: {time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    set_up_logging()

    asyncio.run(main())
