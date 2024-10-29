# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.bedrock.bedrock_prompt_execution_settings import BedrockChatPromptExecutionSettings
from semantic_kernel.connectors.ai.bedrock.services.bedrock_chat_completion import BedrockChatCompletion
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

service_id = "bedrock-chat"
kernel.add_service(BedrockChatCompletion(service_id=service_id, model_id="cohere.command-r-v1:0"))

settings = BedrockChatPromptExecutionSettings(
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    # Cohere Command specific settings: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command-r-plus.html
    extension_data={
        "presence_penalty": 0.5,
        "seed": 5,
    },
)

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)

chat_history = ChatHistory()
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need")


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
            print(str(message[0]), end="", flush=True)
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
