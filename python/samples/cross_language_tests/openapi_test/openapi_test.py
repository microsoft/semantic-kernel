# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.kernel import Kernel
from typing import TYPE_CHECKING, List

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.utils.settings import openai_settings_from_dot_env

kernel = Kernel()

openapi_spec_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "openapi_spec.json")

plugin = kernel.add_plugin_from_openapi(
    plugin_name="LightControl",
    openapi_document_path=openapi_spec_file,
)

api_key, org_id = openai_settings_from_dot_env()
kernel.add_service(
    OpenAIChatCompletion(
        service_id="chat",
        ai_model_id="gpt-3.5-turbo-1106",
        api_key=api_key,
    ),
)

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    ai_model_id="gpt-3.5-turbo-1106",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_call_behavior=FunctionCallBehavior.EnableFunctions(
        auto_invoke=True, filters={"excluded_plugins": ["ChatBot"]}
    ),
)

history = ChatHistory()
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
    print(f"Assistant:> {result}")
    return True


async def main() -> None:
    chatting = True
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  What would you like help with?"
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
