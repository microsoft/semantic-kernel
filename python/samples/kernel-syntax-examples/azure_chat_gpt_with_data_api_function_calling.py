# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureAISearchDataSources,
    AzureChatPromptExecutionSettings,
    AzureDataSources,
    ExtraBody,
)
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_tool_call,
    get_tool_call_object,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

# NOTE:
# AzureOpenAI function calling requires the following models: gpt-35-turbo (1106) or gpt-4 (1106-preview)
# along with the API version: 2023-12-01-preview
# https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling?tabs=python

kernel = sk.Kernel()

# Load Azure OpenAI Settings
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# Create the data source settings
azure_ai_search_settings = sk.azure_aisearch_settings_from_dot_env_as_dict()
az_source = AzureAISearchDataSources(**azure_ai_search_settings)
az_data = AzureDataSources(type="AzureCognitiveSearch", parameters=az_source)
extra = ExtraBody(dataSources=[az_data])
req_settings = AzureChatPromptExecutionSettings(service_id="chat-gpt", extra_body=extra, tool_choice="auto")

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

chat_service = sk_oai.AzureChatCompletion(
    service_id="chat-gpt",
    deployment_name=deployment,
    deployment_name="gpt-35-turbo-16k",
    api_key=api_key,
    endpoint=endpoint,
    api_version="2023-12-01-preview",
    use_extensions=True,
)
kernel.add_service(
    chat_service,
)

plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
kernel.import_plugin_from_prompt_directory("chat-gpt", plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin(TimePlugin(), plugin_name="time")
kernel.import_plugin_from_prompt_directory(plugins_directory, "FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.import_plugin_from_object(TimePlugin(), plugin_name="time")

# enabling or disabling function calling is done by setting the tool_choice parameter for the completion.
# when the tool_choice parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific tool, set the name of that tool in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
prompt_template_config = PromptTemplateConfig(
    template="{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="history", description="The history of the conversation", is_required=True),
        InputVariable(name="request", description="The user input", is_required=True),
    ],
    execution_settings=req_settings,
    template="{{$chat_history}}{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(name="chat_history", description="The history of the conversation", is_required=True),
        InputVariable(name="user_input", description="The user input", is_required=True),
    ],
)

history = ChatHistory()

history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am an AI assistant here to answer your questions.")

arguments = KernelArguments()

chat_function = kernel.create_function_from_prompt(
    plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
)

# calling the chat, you could add a overloaded version of the settings here,
# to enable or disable function calling or set the function calling to a specific plugin.
# see the openai_function_calling example for how to use this with a unrelated function definition
filter = {"exclude_plugin": ["ChatBot"]}
req_settings.tools = get_tool_call_object(kernel, filter)
req_settings.auto_invoke_kernel_functions = True

arguments = KernelArguments(settings=req_settings)


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

    arguments = KernelArguments(request=user_input, execution_settings=req_settings)
    answer = await chat_completion_with_tool_call(
        kernel=kernel,
        arguments=arguments,
        chat_function=chat_function,
    arguments["chat_history"] = history
    arguments["user_input"] = user_input
    answer = await kernel.invoke(
        functions=chat_function,
        arguments=arguments,
    )
    print(f"Mosscap:> {answer}")
    history.add_user_message(user_input)
    history.add_assistant_message(str(answer))
    return True


async def main() -> None:
    print(
        "Welcome to the chat bot!\
\n  Type 'exit' to exit.\
\n  Try a time question to see the function calling in action (i.e. what day is it?)."
        \n  Type 'exit' to exit.\
        \n  Try a time question to see the function calling in action (i.e. what day is it?)."
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
