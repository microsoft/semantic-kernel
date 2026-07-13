# Copyright (c) Microsoft. All rights reserved.

"""OpenAI-compatible multi-model gateway sample using DaoXE.

DaoXE exposes OpenAI Chat Completions at https://daoxe.com/v1 (and other protocols
such as OpenAI Responses / Anthropic Messages for other clients). This sample uses
Semantic Kernel's OpenAIChatCompletion connector with a custom AsyncOpenAI client,
the same pattern as the Ollama / LM Studio samples.

Requirements:
- DAOXE_API_KEY environment variable
- An exact model ID from your DaoXE account catalog (GET /v1/models)

Docs / examples: https://github.com/seven7763/DaoXE-AI
"""

import asyncio
import os

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

system_message = """
You are a helpful assistant. Keep answers concise and practical.
"""

api_key = os.environ.get("DAOXE_API_KEY")
if not api_key:
    raise SystemExit("Set DAOXE_API_KEY to your DaoXE dashboard API key.")

# Exact model ID from your account catalog — do not hardcode a public price list.
ai_model_id = os.environ.get("DAOXE_MODEL")
if not ai_model_id:
    raise SystemExit(
        "Set DAOXE_MODEL to an exact model ID from your DaoXE account catalog "
        '(GET /v1/models), e.g. '
        '`curl -H "Authorization: Bearer $DAOXE_API_KEY" https://daoxe.com/v1/models`.'
    )

kernel = Kernel()
service_id = "daoxe"

openAIClient: AsyncOpenAI = AsyncOpenAI(
    api_key=api_key,
    base_url="https://daoxe.com/v1",
)
kernel.add_service(
    OpenAIChatCompletion(
        service_id=service_id,
        ai_model_id=ai_model_id,
        async_client=openAIClient,
    )
)

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
settings.max_tokens = 256
settings.temperature = 0.7

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)

chat_history = ChatHistory(system_message=system_message)


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    answer = await kernel.invoke(
        chat_function,
        KernelArguments(user_input=user_input, chat_history=chat_history),
    )
    chat_history.add_user_message(user_input)
    chat_history.add_assistant_message(str(answer))
    print(f"Assistant:> {answer}")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
