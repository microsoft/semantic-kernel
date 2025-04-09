# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory


async def main():
    kernel = Kernel()

    service_id = "default"
    chat_service = OpenAIChatCompletion(
        ai_model_id="gpt-3.5-turbo",
        service_id=service_id,
    )
    kernel.add_service(chat_service)

    chat_history = ChatHistory(system_message="Assistant is a large language model")

    plugin_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
    )
    plugin = kernel.add_plugin(plugin_name="sample_plugins", parent_directory=plugin_path)

    result = await kernel.invoke(plugin["Parrot"], count=2, user_message="I love parrots.", chat_history=chat_history)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
