# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os
from functools import reduce

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.kernel import Kernel

logger = logging.getLogger(__name__)


kernel = Kernel()
kernel.add_service(OpenAIChatCompletion(service_id="chat-gpt"))
kernel.add_plugin(
    parent_directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources"), plugin_name="chat"
)


# A filter is a piece of custom code that runs at certain points in the process
# this sample has a filter that is called during Function Invocation for streaming function.
# You can name the function itself with arbitrary names, but the signature needs to be:
# `context, next`
# You are then free to run code before the call to the next filter or the function itself.
# and code afterwards.
# in the specific case of a filter for streaming functions, you need to override the generator
# that is present in the function_result.value as seen below.
@kernel.filter(FilterTypes.FUNCTION_INVOCATION)
async def streaming_exception_handling(context, next):
    await next(context)

    async def override_stream(stream):
        try:
            async for partial in stream:
                yield partial
        except Exception as e:
            yield [StreamingChatMessageContent(role=AuthorRole.ASSISTANT, content=f"Exception caught: {e}")]

    stream = context.result.value
    context.result = FunctionResult(function=context.result.function, value=override_stream(stream))


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
        function_name="chat", plugin_name="chat", user_input=user_input, chat_history=chat_history
    )
    async for message in responses:
        streamed_chunks.append(message[0])
        print(str(message[0]), end="")
    print("")
    chat_history.add_user_message(user_input)
    if streamed_chunks:
        streaming_chat_message = reduce(lambda first, second: first + second, streamed_chunks)
        chat_history.add_message(streaming_chat_message)
    return True


async def main() -> None:
    history = ChatHistory()

    chatting = True
    while chatting:
        chatting = await chat(history)


if __name__ == "__main__":
    asyncio.run(main())
