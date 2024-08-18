# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextToImage
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.image_generation_plugin import ImageGenerationPlugin

system_message = """
You are an image reviewing chat bot. Your name is Mosscap and you have one goal
critiquing images that are supplied.
"""

kernel = Kernel()
dalle3 = OpenAITextToImage(ai_model_id="dall-e-3")
kernel.add_service(dalle3)
service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))
plugin = ImageGenerationPlugin(kernel=kernel, service_id="dall-e-3")
kernel.add_plugin(plugin, "images")

req_settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
req_settings.max_tokens = 2000
req_settings.temperature = 0.7
req_settings.top_p = 0.8
req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["chat"]})

chat_function = kernel.add_function(
    prompt=system_message + """{{$chat_history}}""",
    function_name="chat",
    plugin_name="chat",
    prompt_execution_settings=req_settings,
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

    chat_history = ChatHistory()
    chat_history.add_user_message(user_input)
    answer = await kernel.invoke(function_name="chat", plugin_name="chat", chat_history=chat_history)
    chat_history.add_message(answer.value[0])
    print(f"Mosscap:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
