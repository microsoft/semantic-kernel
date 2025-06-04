# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity import ClientSecretCredential
from booking_sample_settings import BookingSampleSettings
from bookings_plugin.bookings_plugin import BookingsPlugin
from msgraph import GraphServiceClient
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

kernel = Kernel()

service_id = "open_ai"
ai_service = OpenAIChatCompletion(service_id=service_id, ai_model_id="gpt-3.5-turbo")
kernel.add_service(ai_service)

try:
    booking_sample_settings = BookingSampleSettings()
except ValidationError as e:
    raise ServiceInitializationError("Failed to initialize the booking sample settings.") from e

tenant_id = booking_sample_settings.tenant_id
client_id = booking_sample_settings.client_id
client_secret = booking_sample_settings.client_secret
client_secret_credential = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

graph_client = GraphServiceClient(credentials=client_secret_credential, scopes=["https://graph.microsoft.com/.default"])

booking_business_id = booking_sample_settings.business_id
booking_service_id = booking_sample_settings.service_id

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
settings.function_choice_behavior.Auto(filters={"exclude_plugin": ["ChatBot"]})

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
