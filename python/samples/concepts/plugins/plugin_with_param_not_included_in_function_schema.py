# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.const import FUNCTION_SCHEMA_INCLUDE
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function


# The following kernel function in the sample plugin shows how to mark a parameter as not included in the function
# schema. The annotation's metadata, which comes after the specifie type can be in any order -- a string that holds
# the description, or the annotation or a key-value pair of `{FUNCTION_SCHEMA_INCLUDE: False}` to exclude the parameter
# from the function schema.
class MyPlugin:
    @kernel_function(name="my_function")
    def my_function(
        self,
        x: int,
        y: int,
        kernel: Annotated[Kernel, "The Kernel used as an example", {FUNCTION_SCHEMA_INCLUDE: False}],
    ):
        """This is a test function. The only parameters included in the function schema are x and y."""
        return x + y


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
kernel.add_service(OpenAIChatCompletion(service_id="chat"))

plugins_directory = os.path.join(__file__, "../../../../../prompt_template_samples/")
# adding plugins to the kernel
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")
kernel.add_plugin(MyPlugin(), plugin_name="my_plugin")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

# enabling or disabling function calling is done by setting the function_choice_behavior parameter for the
# prompt execution settings. When the function_call parameter is set to "auto" the model will decide which
# function to use, if any. If you only want to use a specific function, configure the filters dict with either:
# 'excluded_plugins', 'included_plugins', 'excluded_functions', or 'included_functions'. For example, the
# format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version does not support this you will get an error.

# Note: the number of responses for auto invoking tool calls is limited to 1.
# If configured to be greater than one, this value will be overridden to 1.
execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Auto(filters={"included_plugins": ["math", "time", "my_plugin"]}),
)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments(settings=execution_settings)


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False
    arguments["user_input"] = user_input
    arguments["chat_history"] = history

    result = await kernel.invoke(chat_function, arguments=arguments)

    print(f"Mosscap:> {result}")

    history.add_user_message(str(user_input))
    history.add_assistant_message(str(result))

    return True


async def main() -> None:
    chatting = True
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  Try a math question to see the function calling in action (i.e. what is 3+3?)."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
