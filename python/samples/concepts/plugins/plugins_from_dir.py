# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextCompletion,
    OpenAITextCompletion,
)
from semantic_kernel.functions import KernelArguments


async def main():
    kernel = Kernel()

    useAzureOpenAI = False
    model = "gpt-35-turbo-instruct" if useAzureOpenAI else "gpt-3.5-turbo-instruct"
    service_id = model

    # Configure AI service used by the kernel
    if useAzureOpenAI:
        kernel.add_service(
            AzureTextCompletion(service_id=service_id),
        )
    else:
        kernel.add_service(
            OpenAITextCompletion(service_id=service_id, ai_model_id=model),
        )

    # note: using plugins from the samples folder
    plugins_directory = os.path.join(
        __file__, "../../../../../prompt_template_samples/"
    )
    plugin = kernel.add_plugin(
        parent_directory=plugins_directory, plugin_name="FunPlugin"
    )

    arguments = KernelArguments(
        input="time travel to dinosaur age", style="super silly"
    )

    result = await kernel.invoke(plugin["Joke"], arguments)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
