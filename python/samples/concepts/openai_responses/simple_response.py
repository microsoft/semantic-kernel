# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIResponseExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.kernel import Kernel

# This sample shows how to create a chatbot. This sample uses the following two main components:
# - a ChatCompletionService: This component is responsible for generating responses to user messages.
# - a ChatHistory: This component is responsible for keeping track of the chat history.
# The chatbot in this sample is called Mosscap, who responds to user messages with long flowery prose.


# You can select from the following chat completion services:
# - Services.OPENAI
# - Services.OPENAI_RESPONSE
# - Services.AZURE_OPENAI
# - Services.AZURE_AI_INFERENCE
# - Services.ANTHROPIC
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.MISTRAL_AI
# - Services.OLLAMA
# - Services.ONNX
# - Services.VERTEX_AI
# - Services.DEEPSEEK
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.OPENAI_RESPONSE)

assert isinstance(request_settings, OpenAIResponseExecutionSettings)  # nosec

# This is the system message that gives the chatbot its personality.
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

# Create a chat history object with the system message.
chat_history = ChatHistory(system_message=system_message)

kernel = Kernel()
kernel.add_plugin(MathPlugin(), plugin_name="math")

request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
request_settings.tools = [{"type": "web_search_preview"}]


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

    # Add the user message to the chat history so that the chatbot can respond to it.
    chat_history.add_user_message(user_input)

    # Get the chat message content from the chat completion service.
    response = await chat_completion_service.get_chat_message_content(
        chat_history=chat_history,
        settings=request_settings,
        kernel=kernel,
    )
    if response:
        print(f"Mosscap:> {response}")

        # Add the chat message to the chat history to keep track of the conversation.
        chat_history.add_message(response)

        for item in response.items:
            if isinstance(item, AnnotationContent):
                print(
                    f"Annotation title={item.title}, {item.url}, start_index={item.start_index} - end_index={item.end_index}"
                )

    return True


async def main() -> None:
    # Start the chat loop. The chat loop will continue until the user types "exit".
    chatting = True
    while chatting:
        chatting = await chat()

    # Sample output:
    # User:> Why is the sky blue in one sentence?
    # Mosscap:> The sky is blue due to the scattering of sunlight by the molecules in the Earth's atmosphere,
    #           a phenomenon known as Rayleigh scattering, which causes shorter blue wavelengths to become more
    #           prominent in our visual perception.


if __name__ == "__main__":
    asyncio.run(main())
