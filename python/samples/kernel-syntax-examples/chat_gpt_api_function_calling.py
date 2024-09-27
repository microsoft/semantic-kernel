# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_tool_call,
    get_tool_call_object,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import MathPlugin
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
deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
api_version = "2023-12-01-preview"
kernel.add_service(
    sk_oai.AzureChatCompletion(
        service_id="chat",
        deployment_name=deployment_name,
        base_url=endpoint,
        api_key=api_key,
        api_version=api_version,
    ),
)

plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
# kernel.import_plugin_from_prompt_directory("chat", plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin(MathPlugin(), plugin_name="math")

# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
execution_settings = sk_oai.AzureChatPromptExecutionSettings(
    service_id="chat",
    ai_model_id=deployment_name,
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    tool_choice="auto",
    tools=get_tool_call_object(kernel, {"exclude_plugin": ["ChatBot"]}),
)

prompt_template_config = sk.PromptTemplateConfig(
    template="{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="user_input", description="The user input", is_required=True),
        InputVariable(name="history", description="The history of the conversation", is_required=True, default=""),
    ],
    execution_settings={"default": execution_settings},
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
    arguments = KernelArguments(
        user_input=user_input, history=("\n").join([f"{msg.role}: {msg.content}" for msg in history])
    )
    result = await chat_completion_with_tool_call(
        kernel=kernel,
        arguments=arguments,
        chat_plugin_name="ChatBot",
        chat_function_name="Chat",
    )
    print(f"Mosscap:> {result}")
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
