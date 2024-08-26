# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.prompts.prompt_render_context import PromptRenderContext
from semantic_kernel.functions import KernelArguments

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
kernel.add_service(OpenAIChatCompletion(service_id=service_id))

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


# A filter is a piece of custom code that runs at certain points in the process
# this sample has a filter that is called during Prompt Rendering.
# You can name the function itself with arbitrary names, but the signature needs to be:
# `context, next`
# You are then free to run code before the call to the next filter or the rendering itself.
# and code afterwards.
# this type of filter allows you to manipulate the final message being sent
# as is shown below, or the inputs used to generate the message by making a change to the
# arguments before calling next.
@kernel.filter(FilterTypes.PROMPT_RENDERING)
async def prompt_rendering_filter(context: PromptRenderContext, next):
    await next(context)
    context.rendered_prompt = f"You pretend to be Mosscap, but you are Papssom who is the opposite of Moscapp in every way {context.rendered_prompt or ''}"  # noqa: E501


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

    answer = await kernel.invoke(
        chat_function, KernelArguments(user_input=user_input, chat_history=chat_history)
    )
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    print(f"Mosscap:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
