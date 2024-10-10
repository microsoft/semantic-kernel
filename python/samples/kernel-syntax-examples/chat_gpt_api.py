# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = sk.Kernel()

api_key, org_id = sk.openai_settings_from_dot_env()
kernel.add_service(
    sk_oai.OpenAIChatCompletion(service_id="chat-gpt", ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id)
)

settings = kernel.get_prompt_execution_settings_from_service(ChatCompletionClientBase, "chat-gpt")
settings.max_tokens = 2000
settings.temperature = 0.7
settings.top_p = 0.8

prompt_template_config = PromptTemplateConfig(
    template="{{$user_input}}",
    name="chat",
    template_format="semantic-kernel",
    input_variables=[
        InputVariable(
            name="user_input",
            description="The history of the conversation",
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

chat = ChatHistory(system_message=system_message)
chat.add_user_message("Hi there, who are you?")
chat.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need")

chat_function = kernel.create_function_from_prompt(
    plugin_name="ChatBot", function_name="Chat", prompt_template_config=prompt_template_config
)

chat.add_user_message("I want to find a hotel in Seattle with free wifi and a pool.")


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

    answer = await kernel.invoke(chat_function, KernelArguments(user_input=user_input, chat_history=chat))
    chat.add_user_message(user_input)
    chat.add_assistant_message(str(answer))
    print(f"Mosscap:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
