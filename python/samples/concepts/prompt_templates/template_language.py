# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.core_plugins import TimePlugin
from semantic_kernel.prompt_template import KernelPromptTemplate, PromptTemplateConfig


async def main():
    kernel = Kernel()

    useAzureOpenAI = False
    model = "gpt-35-turbo" if useAzureOpenAI else "gpt-3.5-turbo-1106"
    service_id = model

    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id=model),
    )

    kernel.add_plugin(TimePlugin(), "time")

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

    kind_of_day = kernel.add_function(
        plugin_name="TimePlugin",
        template=function_definition,
        execution_settings=OpenAIChatPromptExecutionSettings(service_id=service_id, max_tokens=100),
        function_name="kind_of_day",
    )

    print("--- Prompt Function Result ---")
    result = await kernel.invoke(kind_of_day)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
