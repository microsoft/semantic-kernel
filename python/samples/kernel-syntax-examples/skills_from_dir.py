# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

useAzureOpenAI = True
model = "text-davinci-003"
service_id = model

# Configure AI service used by the kernel
if useAzureOpenAI:
    _, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        service_id,
        sk_oai.AzureTextCompletion(
            deployment_name=model, endpoint=endpoint, api_key=api_key
        ),
    )
else:
    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_text_completion_service(
        service_id, sk_oai.OpenAITextCompletion(model, api_key, org_id)
    )


async def main(stream: bool = False) -> None:
    # note: using skills from the samples folder
    skills_directory = os.path.join(__file__, "../../../../samples/skills")
    skill = kernel.import_semantic_skill_from_directory(skills_directory, "FunSkill")
    context = sk.ContextVariables()
    context["input"] = "time travel to dinosaur age"
    if stream:
        async for part in kernel.run_stream_async(skill["Joke"], input_vars=context):
            print(part.content, end="")
        print()

        print("Check updated context:")
        print(context.input)
    else:
        result = await kernel.run_async(skill["Joke"], input_vars=context)
        print(result.variables.input)


if __name__ == "__main__":
    asyncio.run(main(stream=True))
