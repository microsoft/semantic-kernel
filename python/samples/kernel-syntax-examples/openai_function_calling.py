# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import MathPlugin
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

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
kernel.import_plugin_from_prompt_directory("chat", plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin(MathPlugin(), plugin_name="math")

# enabling or disabling function calling is done by setting the function_call parameter for the completion.
# when the function_call parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific function, set the name of that function in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": "Retrieves hotels from the search index based on the parameters provided",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The location of the hotel (i.e. Seattle, WA)",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "The maximum price for the hotel",
                    },
                    "features": {
                        "type": "string",
                        "description": "A comma separated list of features (i.e. beachfront, free wifi, etc.)",
                    },
                },
                "required": ["location"],
            },
        },
    }
]


async def main():
    settings = kernel.get_prompt_execution_settings_from_service(ChatCompletionClientBase, "chat")
    settings.service_id = "chat"
    settings.tools = tools
    settings.tool_choice = "auto"
    settings.max_tokens = 2000
    settings.temperature = 0.7
    settings.top_p = 0.8

    prompt_template_config = PromptTemplateConfig(
        template="{{$user_input}}",
        name="chat",
        template_format="semantic-kernel",
        input_variables=[
            InputVariable(
                name="user_input",
                description="The history of the conversation",
                is_required=True,
                default="",
            ),
            InputVariable(
                name="chat_history",
                description="The history of the conversation",
                is_required=True,
            ),
        ],
        execution_settings=settings,
    )

    chat = ChatHistory(system_message=system_message)
    chat.add_user_message("Hi there, who are you?")
    chat.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need")

    chat_function = kernel.create_function_from_prompt(
        plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
    )

    response = kernel.invoke_stream(
        chat_function,
        KernelArguments(user_input="I want to find a hotel in Seattle with free wifi and a pool.", chat_history=chat),
    )
    messages = []
    tool_call = None
    async for message in response:
        if isinstance(message, FunctionResult):
            # There's been an error, so print it
            print(message)
            return
        current = message[0]
        messages.append(str(current))
        if current.tool_calls:
            if tool_call is None:
                tool_call = current.tool_calls[0]
            else:
                tool_call += current.tool_calls[0]
    if tool_call:
        print(f"Function to be called: {tool_call.function.name}")
        print(f"Function parameters: \n{tool_call.function.parse_arguments()}")
        return
    print("No function was called")
    output = "".join([msg for msg in messages])
    print(f"Output was: {output}")


if __name__ == "__main__":
    asyncio.run(main())
