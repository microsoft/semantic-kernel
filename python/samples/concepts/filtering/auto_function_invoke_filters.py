# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory, ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.filters import AutoFunctionInvocationContext, FilterTypes
from semantic_kernel.functions import FunctionResult, KernelArguments

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

# adding plugins to the kernel
# the math plugin is a core plugin and has the function calling enabled.
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)
# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.

# Note: the number of responses for auto inoking tool calls is limited to 1.
# If configured to be greater than one, this value will be overridden to 1.
execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Auto(filters={"included_plugins": ["math", "time"]}),
)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments(settings=execution_settings)


# A filter is a piece of custom code that runs at certain points in the process
# this sample has a filter that is called during Auto Function Invocation
# this filter will be called for each function call in the response.
# You can name the function itself with arbitrary names, but the signature needs to be:
# `context, next`
# You are then free to run code before the call to the next filter or the function itself.
# if you want to terminate the function calling sequence. set context.terminate to True
@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    print("\nAuto function invocation filter")
    print(f"Function: {context.function.name}")
    print(f"Request sequence: {context.request_sequence_index}")
    print(f"Function sequence: {context.function_sequence_index}")

    # as an example
    function_calls = context.chat_history.messages[-1].items
    print(f"Number of function calls: {len(function_calls)}")
    # if we don't call next, it will skip this function, and go to the next one
    await next(context)
    #############################
    # Note: to simply return the unaltered function results, uncomment the `context.terminate = True` line and
    # comment out the lines starting with `result = context.function_result` through `context.terminate = True`.
    # context.terminate = True
    #############################
    result = context.function_result
    if context.function.plugin_name == "math":
        print("Altering the Math plugin")
        context.function_result = FunctionResult(
            function=result.function,
            value="Stop trying to ask me to do math, I don't like it!",
        )
        context.terminate = True


def print_tool_calls(message: ChatMessageContent) -> None:
    # A helper method to pretty print the tool calls from the message.
    # This is only triggered if auto invoke tool calls is disabled.
    items = message.items
    formatted_tool_calls = []
    for i, item in enumerate(items, start=1):
        if isinstance(item, FunctionCallContent):
            tool_call_id = item.id
            function_name = item.name
            function_arguments = item.arguments
            formatted_str = (
                f"tool_call {i} id: {tool_call_id}\n"
                f"tool_call {i} function name: {function_name}\n"
                f"tool_call {i} arguments: {function_arguments}"
            )
            formatted_tool_calls.append(formatted_str)
    print("Tool calls:\n" + "\n\n".join(formatted_tool_calls))


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

    history.add_user_message(user_input)

    # Check if any result.value is a FunctionResultContent
    if any(isinstance(item, FunctionResultContent) for item in result.value[0].items):
        for fr in result.value[0].items:
            if isinstance(fr, FunctionResultContent):
                print(f"Mosscap:> {fr.result} for function: {fr.name}")
                history.add_assistant_message(str(fr.result))
    elif any(isinstance(item, FunctionCallContent) for item in result.value[0].items):
        # If tools are used, and auto invoke tool calls is False, the response will be of type
        # ChatMessageContent with information about the tool calls, which need to be sent
        # back to the model to get the final response.
        for fcc in result.value[0].items:
            if isinstance(fcc, FunctionCallContent):
                print_tool_calls(fcc)
        history.add_assistant_message(str(result))
    else:
        print(f"Mosscap:> {result}")
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
