# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments

logging.basicConfig(level=logging.WARNING)

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = Kernel()

service_id = "chat-gpt"
chat_service = AzureChatCompletion(
    service_id=service_id,
)
kernel.add_service(chat_service)

req_settings = kernel.get_prompt_execution_settings_from_service_id(
    service_id=service_id
)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()


chat_function = kernel.add_function(
    prompt="""{{system_message}}{% for item in chat_history %}{{ message(item) }}{% endfor %}""",
    function_name="chat",
    plugin_name="chat",
    template_format="jinja2",
    prompt_execution_settings=req_settings,
)

chat_history = ChatHistory()
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message(
    "I am Mosscap, a chat bot. I'm trying to figure out what people need."
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
    chat_history.add_user_message(user_input)
    arguments = KernelArguments(
        system_message=system_message, chat_history=chat_history
    )

    stream = True
    if stream:
        answer = kernel.invoke_stream(
            chat_function,
            arguments=arguments,
        )
        print("Mosscap:> ", end="")
        async for message in answer:
            print(str(message[0]), end="")
        print("\n")
        return True
    answer = await kernel.invoke(
        chat_function,
        arguments=arguments,
    )
    print(f"Mosscap:> {answer}")
    chat_history.add_assistant_message(str(answer))
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
