# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.prompt_template import InputVariable, PromptTemplateConfig

prompt = """
ChatBot can have a conversation with you about any topic.
It can give explicit instructions or say 'I don't know'
when it doesn't know the answer.

{{$chat_history}}

User:> {{$user_input}}
ChatBot:>
"""

kernel = Kernel()

service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
settings.max_tokens = 2000
settings.temperature = 0.7
settings.top_p = 0.8

prompt_template_config = PromptTemplateConfig(
    template=prompt,
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(
            name="user_input",
            description="The user input",
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

chat_history = ChatHistory()
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message(
    "I am Mosscap, a chat bot. I'm trying to figure out what people need"
)

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt_template_config=prompt_template_config,
)


async def chat(chat_history: ChatHistory) -> bool:
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

    print("ChatBot:> ", end="")
    streamed_chunks: list[StreamingChatMessageContent] = []
    responses = kernel.invoke_stream(
        chat_function, user_input=user_input, chat_history=chat_history
    )
    async for message in responses:
        streamed_chunks.append(message[0])
        print(str(message[0]), end="")
    print("")
    chat_history.add_user_message(user_input)
    if streamed_chunks:
        streaming_chat_message = reduce(
            lambda first, second: first + second, streamed_chunks
        )
        chat_history.add_message(streaming_chat_message)
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat(chat_history)


if __name__ == "__main__":
    asyncio.run(main())
