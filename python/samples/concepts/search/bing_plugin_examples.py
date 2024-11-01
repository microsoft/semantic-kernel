# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_plugins import WebSearchEnginePlugin
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import KernelPromptTemplate, PromptTemplateConfig


async def example1(kernel: Kernel, search_plugin_name: str):
    print("======== Bing and Google Search Plugins ========")

    question = "What's the largest building in the world?"
    function = kernel.get_function(plugin_name=search_plugin_name, function_name="search")
    result = await kernel.invoke(function, query=question)

    print(question)
    print(f"----{search_plugin_name}----")
    print(result)


async def example2(kernel: Kernel, service_id: str):
    print("======== Use the Search Plugin to Answer User Questions ========")

    prompt = """
    Answer questions only when you know the facts or the information is provided.
    When you don't have sufficient information you reply with a list of commands to find the information needed.
    When answering multiple questions, use a bullet point list.
    Note: make sure single and double quotes are escaped using a backslash char.

    [COMMANDS AVAILABLE]
    - bing.search

    [INFORMATION PROVIDED]
    {{ $externalInformation }}

    [EXAMPLE 1]
    Question: what's the biggest lake in Italy?
    Answer: Lake Garda, also known as Lago di Garda.

    [EXAMPLE 2]
    Question: what's the biggest lake in Italy? What's the smallest positive number?
    Answer:
    * Lake Garda, also known as Lago di Garda.
    * The smallest positive number is 1.

    [EXAMPLE 3]
    Question: what's Ferrari stock price? Who is the current number one female tennis player in the world?
    Answer:
    {{ '{{' }} bing.search ""what\\'s Ferrari stock price?"" {{ '}}' }}.
    {{ '{{' }} bing.search ""Who is the current number one female tennis player in the world?"" {{ '}}' }}.

    [END OF EXAMPLES]

    [TASK]
    Question: {{ $question }}.
    Answer:
    """
    question = "Who is the most followed person on TikTok right now? What's the exchange rate EUR:USD?"
    print(question)

    oracle = kernel.add_function(
        function_name="oracle",
        plugin_name="OraclePlugin",
        prompt=prompt,
        execution_settings=OpenAIChatPromptExecutionSettings(
            service_id=service_id, max_tokens=150, temperature=0, top_p=1
        ),
    )
    answer = await kernel.invoke(
        oracle,
        question=question,
        externalInformation="",
    )

    result = str(answer)

    if "bing.search" in result:
        prompt_template = KernelPromptTemplate(prompt_template_config=PromptTemplateConfig(template=result))

        print("--- Fetching information from Bing... ---")
        information = await prompt_template.render(kernel, KernelArguments())

        print("Information found:\n")
        print(information)

        answer = await kernel.invoke(oracle, question=question, externalInformation=information)
        print("\n---- Oracle's Answer ----:\n")
        print(answer)
    else:
        print("AI had all of the information, there was no need to query Bing.")


async def main():
    kernel = Kernel()

    model = "gpt-3.5-turbo"
    service_id = model

    kernel.add_service(
        OpenAIChatCompletion(service_id=service_id, ai_model_id=model),
    )

    bing_connector = BingConnector()
    bing = WebSearchEnginePlugin(bing_connector)
    kernel.add_plugin(bing, "bing")

    await example1(kernel, "bing")
    await example2(kernel, service_id)


if __name__ == "__main__":
    asyncio.run(main())
