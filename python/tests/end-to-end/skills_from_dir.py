# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.ai.open_ai as sk_oai

kernel = sk.create_kernel()

useAzureOpenAI = False
model = "text-davinci-002"
service_id = model

# Configure AI backend used by the kernel
if useAzureOpenAI:
    api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.config.add_text_backend(
        service_id, sk_oai.AzureTextCompletion(model, api_key, endpoint)
    )
else:
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.config.add_text_backend(
        service_id, sk_oai.OpenAITextCompletion(model, api_key, org_id)
    )

# note: using skills from the samples folder
skills_directory = os.path.join(__file__, "../../../../samples/skills")
skill = kernel.import_semantic_skill_from_directory(skills_directory, "FunSkill")

result = asyncio.run(
    kernel.run_on_str_async("time travel to dinosaur age", skill["Joke"])
)
print(result)
