# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

# This concept sample shows how to use the OpenAI connector with PZERO's
# OpenAI-compatible endpoint: https://api.pzero.studio/v1
# Get an API key from https://pzero.studio/agents and set PZERO_API_KEY.

system_message = """
You are a helpful and concise AI assistant.
"""

kernel = Kernel()

service_id = "pzero-deepseek"

api_key = os.environ.get("PZERO_API_KEY", "your-pzero-api-key")
endpoint = "https://api.pzero.studio/v1"
model_id = "deepseek-v4-flash"

open_ai_client: AsyncOpenAI = AsyncOpenAI(
    api_key=api_key,
    base_url=endpoint,
)
kernel.add_service(OpenAIChatCompletion(service_id=service_id, ai_model_id=model_id, async_client=open_ai_client))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
settings.max_tokens = 1000
settings.temperature = 0.7

chat_function = kernel.add_function(
    plugin_name="ChatBot",
    function_name="Chat",
    prompt="{{$chat_history}}{{$user_input}}",
    template_format="semantic-kernel",
    prompt_execution_settings=settings,
)


async def main() -> None:
    chat_history = ChatHistory(system_message=system_message)
    user_message = "What is Semantic Kernel in one sentence?"
    chat_history.add_user_message(user_message)

    answer = await kernel.invoke(chat_function, KernelArguments(user_input=user_message, chat_history=chat_history))
    print(f"User:> {user_message}")
    print(f"Assistant:> {answer}")


if __name__ == "__main__":
    asyncio.run(main())
