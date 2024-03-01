# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.utils import (
    get_tool_call_object,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable

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

kernel = sk.Kernel()

# Note: the underlying gpt-35/gpt-4 model version needs to be at least version 0613 to support tools.
api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_service(
    sk_oai.OpenAIChatCompletion(
        service_id="chat",
        ai_model_id="gpt-3.5-turbo-1106",
        api_key=api_key,
    ),
)

plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
# kernel.import_plugin_from_prompt_directory("chat", plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin_from_object(MathPlugin(), plugin_name="math")
kernel.import_plugin_from_object(TimePlugin(), plugin_name="time")

# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
execution_settings = sk_oai.OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    tool_choice="auto",
    tools=get_tool_call_object(kernel, {"exclude_plugin": ["ChatBot"]}),
    auto_invoke_kernel_functions=True,
    max_auto_invoke_attempts=3,
    number_of_responses=2,
)

prompt_template_config = sk.PromptTemplateConfig(
    template="{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="user_input", description="The user input", is_required=True),
        InputVariable(name="chat_history", description="The history of the conversation", is_required=True),
    ],
    execution_settings={"chat": execution_settings},
)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments()

chat_function = kernel.create_function_from_prompt(
    prompt_template_config=prompt_template_config,
    plugin_name="ChatBot",
    function_name="Chat",
)


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

    stream = True
    if stream:
        response = kernel.invoke_stream(
            chat_function,
            return_function_results=False,
            user_input=user_input,
            chat_history=history,
        )

        print("Mosscap:> ", end="")
        async for message in response:
            print(str(message[0]), end="")
        print("\n")
    else:
        result = await kernel.invoke(chat_function, user_input=user_input, chat_history=history)
        # Check if there are more than one item in the list
        if len(result.value) > 1:
            joined_result = ", ".join([f"Result{i+1}: {value}" for i, value in enumerate(result.value)])
        else:
            joined_result = f"{result[0]}"
        print(f"Mosscap:> {joined_result}")
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
