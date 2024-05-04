# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity import ClientSecretCredential
from bookings_plugin.bookings_plugin import BookingsPlugin
from dotenv import dotenv_values
from msgraph import GraphServiceClient

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.utils import get_tool_call_object
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import booking_sample_settings_from_dot_env_as_dict, openai_settings_from_dot_env

kernel = Kernel()

service_id = "open_ai"
api_key, _ = openai_settings_from_dot_env()
ai_service = OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo-1106", api_key=api_key)
kernel.add_service(ai_service)

client_secret_credential = ClientSecretCredential(**booking_sample_settings_from_dot_env_as_dict())

graph_client = GraphServiceClient(credentials=client_secret_credential, scopes=["https://graph.microsoft.com/.default"])

config = dotenv_values(".env")
booking_business_id = config.get("BOOKING_SAMPLE_BUSINESS_ID")
assert booking_business_id, "BOOKING_SAMPLE_BUSINESS_ID is not set in .env file"
booking_service_id = config.get("BOOKING_SAMPLE_SERVICE_ID")
assert booking_service_id, "BOOKING_SAMPLE_SERVICE_ID is not set in .env file"

bookings_plugin = BookingsPlugin(
    graph_client=graph_client,
    booking_business_id=booking_business_id,
    booking_service_id=booking_service_id,
)

kernel.add_plugin(bookings_plugin, "BookingsPlugin")

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
)

settings: OpenAIChatPromptExecutionSettings = kernel.get_prompt_execution_settings_from_service_id(
    service_id, ChatCompletionClientBase
)
settings.max_tokens = 2000
settings.temperature = 0.1
settings.top_p = 0.8
settings.auto_invoke_kernel_functions = True
settings.tool_choice = "auto"
settings.tools = get_tool_call_object(kernel, {"exclude_plugin": ["ChatBot"]})

chat_history = ChatHistory(
    system_message="When responding to the user's request to book a table, include the reservation ID."
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

    # Note the reservation returned contains an ID. That ID can be used to cancel the reservation,
    # when the bookings API supports it.
    answer = await kernel.invoke(
        chat_function, KernelArguments(settings=settings, user_input=user_input, chat_history=chat_history)
    )
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    print(f"Assistant:> {answer}")
    return True


async def main() -> None:
    chatting = True
    print(
        "Welcome to your Restaurant Booking Assistant.\
        \n  Type 'exit' to exit.\
        \n  Please enter the following information to book a table: the restaurant, the date and time, \
        \n the number of people, your name, phone, and email. You may ask me for help booking a table, \
        \n listing reservations, or cancelling a reservation. When cancelling please provide the reservation ID."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
