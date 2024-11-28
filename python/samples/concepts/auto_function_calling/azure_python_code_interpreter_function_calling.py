# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin import SessionsPythonTool
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

kernel = Kernel()

service_id = "sessions-tool"
chat_service = AzureChatCompletion(
    service_id=service_id,
)
kernel.add_service(chat_service)

sessions_tool = SessionsPythonTool()

kernel.add_plugin(sessions_tool, "SessionsTool")
kernel.add_plugin(TimePlugin(), "Time")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

req_settings = AzureChatPromptExecutionSettings(service_id=service_id, tool_choice="auto")

req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]})

arguments = KernelArguments(settings=req_settings)

history = ChatHistory()


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
        \n  Try a Python code execution question to see the function calling in action (i.e. what is 1+1?)."
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
