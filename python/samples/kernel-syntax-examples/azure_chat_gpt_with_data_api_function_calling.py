# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Tuple

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.request_settings.azure_chat_request_settings import (
    AzureAISearchDataSources,
    AzureChatRequestSettings,
    AzureDataSources,
    ExtraBody,
)
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_function_call,
    get_function_calling_object,
)
from semantic_kernel.core_plugins.time_plugin import TimePlugin

kernel = sk.Kernel()

# Load Azure OpenAI Settings
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Create the data source settings
azure_ai_search_settings = sk.azure_aisearch_settings_from_dot_env_as_dict()
az_source = AzureAISearchDataSources(**azure_ai_search_settings)
az_data = AzureDataSources(type="AzureCognitiveSearch", parameters=az_source)
extra = ExtraBody(dataSources=[az_data])
req_settings = AzureChatRequestSettings(extra_body=extra)

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

chat_service = sk_oai.AzureChatCompletion(
    deployment_name=deployment,
    api_key=api_key,
    endpoint=endpoint,
    api_version="2023-12-01-preview",
    use_extensions=True,
)
kernel.add_chat_service(
    "chat-gpt",
    chat_service,
)

plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
kernel.import_semantic_plugin_from_directory(plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin(TimePlugin(), plugin_name="time")

# enabling or disabling function calling is done by setting the tool_choice parameter for the completion.
# when the tool_choice parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific tool, set the name of that tool in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
req_settings.tool_choice = "auto"
prompt_config = sk.PromptTemplateConfig(execution_settings=req_settings)
prompt_template = OpenAIChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message("I am an AI assistant here to answer your questions.")

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)

# calling the chat, you could add a overloaded version of the settings here,
# to enable or disable function calling or set the function calling to a specific plugin.
# see the openai_function_calling example for how to use this with a unrelated function definition
filter = {"exclude_plugin": ["ChatBot"]}
functions = get_function_calling_object(kernel, filter)


async def chat(context: sk.SKContext) -> Tuple[bool, sk.SKContext]:
    try:
        user_input = input("User:> ")
        context.variables["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False, None
    except EOFError:
        print("\n\nExiting chat...")
        return False, None

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False, None

    context = await chat_completion_with_function_call(
        kernel,
        chat_plugin_name="ChatBot",
        chat_function_name="Chat",
        context=context,
        functions=functions,
    )
    print(f"Assistant:> {context.result}")
    return True, context


async def main() -> None:
    chatting = True
    context = kernel.create_new_context()
    print(
        "Welcome to the chat bot!\
\n  Type 'exit' to exit.\
\n  Try a time question to see the function calling in action (i.e. what day is it?)."
    )
    while chatting:
        chatting, context = await chat(context)


if __name__ == "__main__":
    asyncio.run(main())
