# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import (
    ChatHistory,
    ChatMessageContent,
    ImageContent,
    TextContent,
)

logging.basicConfig(level=logging.WARNING)

system_message = """
You are an image reviewing chat bot. Your name is Mosscap and you have one goal
critiquing images that are supplied.
"""

kernel = Kernel()

service_id = "chat-gpt"
chat_service = AzureChatCompletion(service_id=service_id)
kernel.add_service(chat_service)

req_settings = kernel.get_prompt_execution_settings_from_service_id(
    service_id=service_id
)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(
    filters={"excluded_plugins": []}
)

chat_function = kernel.add_function(
    prompt=system_message + """{{$chat_history}}""",
    function_name="chat",
    plugin_name="chat",
    prompt_execution_settings=req_settings,
)


async def chat(uri: str | None = None, image_path: str | None = None) -> bool:
    history = ChatHistory()
    if uri:
        history.add_message(
            ChatMessageContent(
                role="user",
                items=[
                    TextContent(text="What is in this image?"),
                    ImageContent(uri=uri),
                ],
            )
        )
    elif image_path:
        history.add_message(
            ChatMessageContent(
                role="user",
                items=[
                    TextContent(text="What is in this image?"),
                    ImageContent.from_image_path(image_path),
                ],
            )
        )
    else:
        history.add_user_message("Hi there, who are you?")
    answer = kernel.invoke_stream(
        chat_function,
        chat_history=history,
    )
    print("Mosscap:> ", end="")
    async for message in answer:
        print(str(message[0]), end="")
    print("\n")


async def main() -> None:
    print("Get a description of a image from a URL.")
    await chat(
        uri="https://upload.wikimedia.org/wikipedia/commons/d/d5/Half-timbered_mansion%2C_Zirkel%2C_East_view.jpg"
    )
    print("Get a description of the same image but now from a local file!")
    await chat(image_path="samples/concepts/resources/sample_image.jpg")


if __name__ == "__main__":
    asyncio.run(main())
