# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from dotenv import load_dotenv

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict

logging.basicConfig(level=logging.INFO)

load_dotenv()

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = sk.Kernel()

chat_service = sk_oai.AzureChatCompletion(**azure_openai_settings_from_dot_env_as_dict(include_api_version=True))
kernel.add_chat_service("chat-gpt", chat_service)

## there are three ways to create the request settings in code: # noqa: E266

## 1. create the request settings from the base class: # noqa: E266
# from semantic_kernel.connectors.ai.chat_completion_client_base import PromptExecutionSettings
# req_settings = PromptExecutionSettings(extension_data = { "max_tokens": 2000, "temperature": 0.7, "top_p": 0.8} )
## This method (using the PromptExecutionSettings base class) is the most generic, and it allows you to store request settings for different services in the same extension_data field. There are two downsides to this approach: the specific request setting class will be created dynamically for each call, this is overhead when using just a single service. and the request settings are not type checked, so you will receive error messages once the dynamic creation of the request settings class fails. # noqa: E501 E266

## 2. create the request settings directly for the service you are using: # noqa: E266
# req_settings = sk_oai.AzureChatPromptExecutionSettings(max_tokens=2000, temperature=0.7, top_p=0.8)
## The second method is useful when you are using a single service, and you want to have type checking on the request settings or when you are using multiple instances of the same type of service, for instance gpt-35-turbo and gpt-4, both in openai and both for chat.  # noqa: E501 E266

## 3. create the request settings from the kernel based on the registered service class: # noqa: E266
req_settings = kernel.get_prompt_execution_settings_from_service(ChatCompletionClientBase, "chat-gpt")
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
## The third method is the most specific as the returned request settings class is the one that is registered for the service and has some fields already filled in, like the service_id and ai_model_id. # noqa: E501 E266


prompt_config = sk.PromptTemplateConfig(execution_settings=req_settings)

prompt_template = sk.ChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)

prompt_template.add_system_message(system_message)
prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)


async def chat() -> bool:
    context_vars = sk.ContextVariables()
    try:
        user_input = input("User:> ")
        if user_input == "":
            context_vars["user_input"] = "what is openai?"
        else:
            context_vars["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    stream = False
    if stream:
        answer = kernel.run_stream(chat_function, input_vars=context_vars)
        print("Mosscap:> ", end="")
        async for message in answer:
            print(str(message[0]), end="")
        print("\n")
        return True
    answer = await kernel.run(chat_function, input_vars=context_vars)
    print(f"Mosscap:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
