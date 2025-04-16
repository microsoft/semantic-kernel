# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

import semantic_kernel as sk
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    AzureAISearchDataSource,
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
    ExtraBody,
)
from semantic_kernel.connectors.memory.azure_cognitive_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins import TimePlugin
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig

logging.basicConfig(level=logging.DEBUG)
# NOTE:
# AzureOpenAI function calling requires the following models: gpt-35-turbo (1106) or gpt-4 (1106-preview)
# along with the API version: 2024-02-15-preview
# https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling?tabs=python

kernel = sk.Kernel()

# Create the data source settings
azure_ai_search_settings = AzureAISearchSettings()
az_source = AzureAISearchDataSource(parameters=azure_ai_search_settings.model_dump())
extra = ExtraBody(data_sources=[az_source])
req_settings = AzureChatPromptExecutionSettings(service_id="chat-gpt", extra_body=extra, tool_choice="auto")

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

chat_service = AzureChatCompletion(
    service_id="chat-gpt",
)
kernel.add_service(
    chat_service,
)

plugins_directory = os.path.join(__file__, "../../../../../prompt_template_samples/")
# adding plugins to the kernel
# the joke plugin in the FunPlugins is a semantic plugin and has the function calling disabled.
kernel.add_plugin(parent_directory=plugins_directory, plugin_name="FunPlugin")
# the math plugin is a core plugin and has the function calling enabled.
kernel.add_plugin(TimePlugin(), plugin_name="time")

# enabling or disabling function calling is done by setting the tool_choice parameter for the completion.
# when the tool_choice parameter is set to "auto" the model will decide which function to use, if any.
# if you only want to use a specific tool, set the name of that tool in this parameter,
# the format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version do not support this you will get an error.
prompt_template_config = PromptTemplateConfig(
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

chat_function = kernel.add_function(
    plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
)

# calling the chat, you could add a overloaded version of the settings here,
# to enable or disable function calling or set the function calling to a specific plugin.
# see the openai_function_calling example for how to use this with a unrelated function definition
req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]})

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

    arguments["chat_history"] = history
    arguments["user_input"] = user_input
    answer = await kernel.invoke(
        function=chat_function,
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
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
