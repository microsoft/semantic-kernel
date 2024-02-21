# Copyright (c) Microsoft. All rights reserved.
import logging

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.utils.logging import setup_logging
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def main():
    setup_logging()

    # Set the logging level for  semantic_kernel.kernel to DEBUG.
    logging.getLogger("kernel").setLevel(logging.DEBUG)

    kernel = sk.Kernel()

    api_key, org_id = sk.openai_settings_from_dot_env()

    kernel.add_service(OpenAIChatCompletion(service_id="chat-gpt", ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id))

    plugin = kernel.import_plugin_from_prompt_directory(service_id="chat-gpt",parent_directory="../../samples/plugins", plugin_directory_name="FunPlugin")

    joke_function = plugin["Joke"]

    result = await kernel.invoke(joke_function, KernelArguments(input="time travel to dinosaur age"))

    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
