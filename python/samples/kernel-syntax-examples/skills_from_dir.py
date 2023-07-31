# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

useAzureOpenAI = False
model = "text-davinci-002"
service_id = model

# Configure AI service used by the kernel
if useAzureOpenAI:
    api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        service_id, sk_oai.AzureTextCompletion(model, api_key, endpoint)
    )
else:
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        service_id, sk_oai.OpenAITextCompletion(model, api_key, org_id)
    )
# note: using skills from the samples folder
skills_directory = os.path.join(__file__, "../../../../prompts/samples")
skill = kernel.import_semantic_skill_from_directory(skills_directory, "FunPlugin")

result = asyncio.run(
    kernel.run_async(skill["Joke"], input_str="time travel to dinosaur age")
)
print(result)
