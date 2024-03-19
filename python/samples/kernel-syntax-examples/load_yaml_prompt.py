# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import (
    openai_settings_from_dot_env,
)


async def main():
    kernel = Kernel()

    api_key, _ = openai_settings_from_dot_env()

    service_id = "default"
    chat_service = OpenAIChatCompletion(
        ai_model_id="gpt-4-0613",
        service_id=service_id,
        api_key=api_key,
    )
    kernel.add_service(chat_service)

    chat_history = ChatHistory(system_message="Assistant is a large language model")

    cur_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
    plugin = kernel.import_plugin_from_prompt_directory(cur_dir, "sample_plugins")

    result = await kernel.invoke(plugin["Parrot"], count=2, user_message="I love parrots.", chat_history=chat_history)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
