# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework.openai import OpenAIResponsesClient

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.core_plugins import TimePlugin
from semantic_kernel.functions import KernelFunctionFromPrompt
from semantic_kernel.prompt_template import KernelPromptTemplate, PromptTemplateConfig


async def main():
    kernel = Kernel()

    service_id = "template_language"
    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id),
    )

    kernel.add_plugin(TimePlugin(), "time")

    function_definition = """
    Today is: {{time.date}}
    Current time is: {{time.time}}

    Answer to the following questions using JSON syntax, including the data used.
    Is it morning, afternoon, evening, or night (morning/afternoon/evening/night)?
    Is it weekend time (weekend/not weekend)?
    """

    print("--- Rendered Prompt ---")
    prompt_template_config = PromptTemplateConfig(template=function_definition)
    prompt_template = KernelPromptTemplate(prompt_template_config=prompt_template_config)
    rendered_prompt = await prompt_template.render(kernel, arguments=None)
    print(rendered_prompt)

    function = KernelFunctionFromPrompt(
        description="Determine the kind of day based on the current time and date.",
        plugin_name="TimePlugin",
        prompt_execution_settings=OpenAIChatPromptExecutionSettings(service_id=service_id, max_tokens=100),
        function_name="kind_of_day",
        prompt_template=prompt_template,
    ).as_agent_framework_tool(kernel=kernel)

    print("--- Prompt Function Result ---")
    response = await (
        OpenAIResponsesClient(model_id="gpt-5-nano").create_agent(tools=function).run("What kind of day is it?")
    )
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
