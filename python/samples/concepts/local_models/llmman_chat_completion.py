# Copyright (c) Microsoft. All rights reserved.


import asyncio

from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

# This concept sample shows how to use the Ollama connector with a local model
# running in llmman (https://github.com/llmmanorg/llmman), which serves the
# Ollama API on port 17434, so only the host differs.
# Requires `pip install "semantic-kernel[ollama]"`. Install llmman per its
# README, then run `llmman serve` and `llmman pull gemma4`.

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""

kernel = Kernel()

service_id = "local-gpt"

kernel.add_service(OllamaChatCompletion(service_id=service_id, ai_model_id="gemma4", host="http://localhost:17434"))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
# Model specific settings go in the options dictionary, same as with Ollama.
settings.options = {"num_predict": 2000, "temperature": 0.7, "top_p": 0.8}

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)

chat_history = ChatHistory(system_message=system_message)
chat_history.add_user_message("Hi there, who are you?")
chat_history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need")


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

    answer = await kernel.invoke(chat_function, KernelArguments(user_input=user_input, chat_history=chat_history))
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
