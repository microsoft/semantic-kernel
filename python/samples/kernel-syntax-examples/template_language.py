# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.core_plugins import (
    TimePlugin,
)
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


async def main():
    kernel = sk.Kernel()

    useAzureOpenAI = False
    model = "gpt-35-turbo" if useAzureOpenAI else "gpt-3.5-turbo-1106"
    service_id = model

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_service(
        sk_oai.OpenAIChatCompletion(service_id=service_id, ai_model_id=model, api_key=api_key, org_id=org_id),
    )

    kernel.import_plugin(TimePlugin(), "time")
    kernel.import_plugin_from_object(TimePlugin(), "time")

    function_definition = """
    Today is: {{time.Date}}
    Current time is: {{time.Time}}

    Answer to the following questions using JSON syntax, including the data used.
    Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
    Is it weekend time (weekend/not weekend)?
    """

    print("--- Rendered Prompt ---")
    prompt_template_config = PromptTemplateConfig(template=function_definition)
    prompt_template = KernelPromptTemplate(prompt_template_config)
    rendered_prompt = await prompt_template.render(kernel, arguments=None)
    print(rendered_prompt)

    kind_of_day = kernel.create_function_from_prompt(
        plugin_name="TimePlugin",
        template=function_definition,
        execution_settings=sk_oai.OpenAIChatPromptExecutionSettings(service_id=service_id, max_tokens=100),
        function_name="kind_of_day",
    )

    print("--- Prompt Function Result ---")
    result = await kernel.invoke(kind_of_day)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
