# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.mistral_ai import MistralAIChatCompletion
from semantic_kernel.contents import ChatHistory

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = Kernel()

service_id = "mistral-ai-chat"
kernel.add_service(MistralAIChatCompletion(service_id=service_id))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
settings.max_tokens = 2000
settings.temperature = 0.7
settings.top_p = 0.8

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)

chat_history = ChatHistory(system_message=system_message)
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message(
    "I am Mosscap, a chat bot. I'm trying to figure out what people need"
)
chat_history.add_user_message(
    "I want to find a hotel in Seattle with free wifi and a pool."
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
        chunks = kernel.invoke_stream(
            chat_function,
            user_input=user_input,
            chat_history=chat_history,
        )
        print("Mosscap:> ", end="")
        answer = ""
        async for message in chunks:
            print(str(message[0]), end="")
            answer += str(message[0])
        print("\n")
    else:
        answer = await kernel.invoke(
            chat_function,
            user_input=user_input,
            chat_history=chat_history,
        )
        print(f"Mosscap:> {answer}")

    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
