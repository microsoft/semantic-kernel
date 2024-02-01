# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

useAzureOpenAI = False
model = "gpt-35-turbo-instruct" if useAzureOpenAI else "gpt-3.5-turbo-instruct"
service_id = model

# Configure AI service used by the kernel
if useAzureOpenAI:
    deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        service_id,
        sk_oai.AzureTextCompletion(deployment_name=model, api_key=api_key, endpoint=endpoint),
    )
else:
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        service_id,
        sk_oai.OpenAITextCompletion(ai_model_id=model, api_key=api_key, org_id=org_id),
    )

# note: using plugins from the samples folder
plugins_directory = os.path.join(__file__, "../../../../samples/plugins")
plugin = kernel.import_semantic_plugin_from_directory(plugins_directory, "FunPlugin")

result = asyncio.run(kernel.run(plugin["Joke"], input_str="time travel to dinosaur age"))
print(result)
