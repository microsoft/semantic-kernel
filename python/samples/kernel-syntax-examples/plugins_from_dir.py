# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def main():
    kernel = sk.Kernel()

    useAzureOpenAI = False
    model = "gpt-35-turbo-instruct" if useAzureOpenAI else "gpt-3.5-turbo-instruct"
    service_id = model

    # Configure AI service used by the kernel
    if useAzureOpenAI:
        deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        kernel.add_service(
            sk_oai.AzureTextCompletion(
                service_id=service_id, deployment_name=model, api_key=api_key, endpoint=endpoint
            ),
        )
    else:
        api_key, org_id = sk.openai_settings_from_dot_env()
        kernel.add_service(
            sk_oai.OpenAITextCompletion(service_id=service_id, ai_model_id=model, api_key=api_key, org_id=org_id),
        )

    # note: using plugins from the samples folder
    plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
    plugin = kernel.import_plugin_from_prompt_directory(service_id, plugins_directory, "FunPlugin")

    arguments = KernelArguments(input="time travel to dinosaur age", style="super silly")

    result = await kernel.invoke(plugin["Joke"], arguments)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
