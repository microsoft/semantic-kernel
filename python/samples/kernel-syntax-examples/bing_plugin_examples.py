# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_plugins import WebSearchEnginePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


async def example1(kernel: sk.Kernel, search_plugin_name: str):
    print("======== Bing and Google Search Plugins ========")

    question = "What's the largest building in the world?"
    function = kernel.plugins[search_plugin_name]["search"]
    result = await kernel.invoke(function, query=question)

    print(question)
    print(f"----{search_plugin_name}----")
    print(result)


async def example2(kernel: sk.Kernel, service_id: str):
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

    oracle = kernel.create_function_from_prompt(
        function_name="oracle",
        plugin_name="OraclePlugin",
        template=prompt,
        execution_settings=sk_oai.OpenAIChatPromptExecutionSettings(
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
        prompt_template = KernelPromptTemplate(PromptTemplateConfig(template=result))

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
    kernel = sk.Kernel()

    model = "gpt-3.5-turbo-1106"
    service_id = model

    api_key, org_id = sk.openai_settings_from_dot_env()
    kernel.add_service(
        sk_oai.OpenAIChatCompletion(service_id=service_id, ai_model_id=model, api_key=api_key, org_id=org_id),
    )

    bing_api_key = sk.bing_search_settings_from_dot_env()
    assert bing_api_key is not None

    bing_connector = BingConnector(api_key=bing_api_key)
    bing = WebSearchEnginePlugin(bing_connector)
    kernel.import_plugin(bing, "bing")
    kernel.import_plugin_from_object(bing, "bing")

    await example1(kernel, "bing")
    await example2(kernel, service_id)


if __name__ == "__main__":
    asyncio.run(main())
