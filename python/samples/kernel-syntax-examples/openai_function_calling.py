# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_chat_message import (
    OpenAIChatMessage,
)
from semantic_kernel.core_plugins import MathPlugin

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
kernel.add_chat_service(
    "gpt-3.5-turbo",
    sk_oai.OpenAIChatCompletion(
        ai_model_id="gpt-3.5-turbo-1106",
        api_key=api_key,
    ),
)

plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
kernel.import_semantic_plugin_from_directory(plugins_directory, "FunPlugin")
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

prompt_config = sk.PromptTemplateConfig.from_execution_settings(
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    tool_choice="auto",
    tools=tools,
)
prompt_template = sk.ChatPromptTemplate[OpenAIChatMessage](
    "{{$user_input}}", kernel.prompt_template_engine, prompt_config
)
prompt_template.add_system_message(system_message)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
# define the functions available


async def main() -> None:
    context = kernel.create_new_context()
    context.variables["user_input"] = "I want to find a hotel in Seattle with free wifi and a pool."

    context = await chat_function.invoke_async(context=context)
    if function_call := context.objects.get("function_call"):
        print(f"Function to be called: {function_call.name}")
        print(f"Function parameters: \n{function_call.arguments}")
    else:
        print("No function was called")
        print(f"Output was: {str(context)}")


if __name__ == "__main__":
    asyncio.run(main())
