# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import TYPE_CHECKING

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    pass


system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You are also a math wizard,
especially for adding and subtracting.
You also excel at joke telling, where your tone is often sarcastic.
Once you have the answer I am looking for,
you will return a full answer to me as soon as possible.
"""

kernel = Kernel()

# Note: the underlying gpt-35/gpt-4 model version needs to be at least version 0613 to support tools.
kernel.add_service(AzureChatCompletion(service_id="chat"))

plugins_directory = os.path.join(__file__, "../../../../../prompt_template_samples/")
# adding plugins to the kernel
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

# Enabling or disabling function calling is done by setting the `function_choice_behavior` attribute for the
# prompt execution settings. When the function_call parameter is set to "auto" the model will decide which
# function to use, if any.
#
# There are two ways to define the `function_choice_behavior` parameter:
# 1. Using the type string as `"auto"`, `"required"`, or `"none"`. For example:
#   configure `function_choice_behavior="auto"` parameter directly in the execution settings.
# 2. Using the FunctionChoiceBehavior class. For example:
#   `function_choice_behavior=FunctionChoiceBehavior.Auto()`.
# Both of these configure the `auto` tool_choice and all of the available plugins/functions
# registered on the kernel. If you want to limit the available plugins/functions, you must
# configure the `filters` dictionary attribute for each type of function choice behavior.
# For example:
#
# from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# function_choice_behavior = FunctionChoiceBehavior.Auto(
#     filters={"included_functions": ["time-date", "time-time", "math-Add"]}
# )
#
# The filters attribute allows you to specify either: `included_functions`, `excluded_functions`,
#  `included_plugins`, or `excluded_plugins`.

# Note: the number of responses for auto invoking tool calls is limited to 1.
# If configured to be greater than one, this value will be overridden to 1.
execution_settings = AzureChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Auto(),
)

arguments = KernelArguments(settings=execution_settings)


async def main() -> None:
    user_input = "What is the current hour plus 10?"
    print(f"User:> {user_input}")

    result = await kernel.invoke_prompt(prompt=user_input, arguments=arguments)

    print(f"Mosscap:> {result}")

    print("\nChat history:")
    chat_history: ChatHistory = result.metadata["messages"]
    print(chat_history.serialize())


if __name__ == "__main__":
    asyncio.run(main())
