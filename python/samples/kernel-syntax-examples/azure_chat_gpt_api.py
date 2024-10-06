# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from dotenv import load_dotenv

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict

logging.basicConfig(level=logging.INFO)

load_dotenv()
import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env_as_dict

logging.basicConfig(level=logging.WARNING)

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = sk.Kernel()

service_id = "chat-gpt"
chat_service = sk_oai.AzureChatCompletion(
    service_id=service_id, **azure_openai_settings_from_dot_env_as_dict(include_api_version=True)
)
kernel.add_service(chat_service)

## there are three ways to create the request settings in code: # noqa: E266
## Note: the prompt_execution_settings are a dictionary with the service_id as the key and the request settings as the value. # noqa: E501

## 1. create the request settings from the base class: # noqa: E266
# from semantic_kernel.connectors.ai.chat_completion_client_base import PromptExecutionSettings
# req_settings = PromptExecutionSettings(extension_data = { "max_tokens": 2000, "temperature": 0.7, "top_p": 0.8} )
## This method (using the PromptExecutionSettings base class) is the most generic, and it allows you to store request settings for different services in the same extension_data field. There are two downsides to this approach: the specific request setting class will be created dynamically for each call, this is overhead when using just a single service. and the request settings are not type checked, so you will receive error messages once the dynamic creation of the request settings class fails. # noqa: E501 E266

## 2. create the request settings directly for the service you are using: # noqa: E266
# req_settings = sk_oai.AzureChatPromptExecutionSettings(max_tokens=2000, temperature=0.7, top_p=0.8)

## The second method is useful when you are using a single service, and you want to have type checking on the request settings or when you are using multiple instances of the same type of service, for instance gpt-35-turbo and gpt-4, both in openai and both for chat.  # noqa: E501 E266
## 3. create the request settings from the kernel based on the registered service class: # noqa: E266
req_settings = kernel.get_service(service_id).get_prompt_execution_settings_class()(service_id=service_id)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
## The third method is the most specific as the returned request settings class is the one that is registered for the service and has some fields already filled in, like the service_id and ai_model_id. # noqa: E501 E266

prompt_template_config = sk.PromptTemplateConfig(
    template=system_message
    + """ Summarize the on-going chat history: {{$chat_history}} and respond to this statement: {{$request}}""",
    name="chat",
    input_variables=[
        InputVariable(name="request", description="The user input", is_required=True),
        InputVariable(name="chat_history", description="The history of the conversation", is_required=True),
    ],
    execution_settings=req_settings,
req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
req_settings.auto_invoke_kernel_functions = True
## The third method is the most specific as the returned request settings class is the one that is registered for the service and has some fields already filled in, like the service_id and ai_model_id. # noqa: E501 E266


chat_function = kernel.create_function_from_prompt(
    prompt=system_message + """{{$chat_history}}{{$user_input}}""",
    function_name="chat",
    plugin_name="chat",
    prompt_execution_settings=req_settings,
)

history = ChatHistory()
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

chat_function = kernel.create_function_from_prompt(prompt_template_config=prompt_template_config)


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
        answer = kernel.invoke_stream(
            chat_function,
            request=user_input,
            user_input=user_input,
            chat_history=history,
        )
        print("Mosscap:> ", end="")
        async for message in answer:
            print(str(message[0]), end="")
        print("\n")
        return True
    answer = await kernel.invoke(
        chat_function,
        request=user_input,
        user_input=user_input,
        chat_history=history,
    )
    print(f"Mosscap:> {answer}")
    history.add_user_message(user_input)
    history.add_assistant_message(str(answer))
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
