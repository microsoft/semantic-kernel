# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.core_plugins import WebSearchEnginePlugin
from semantic_kernel.prompt_template import PromptTemplateConfig


async def main():
    kernel = Kernel()
    service_id = "chat-gpt"
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    connector = BingConnector()
    web_plugin = kernel.add_plugin(WebSearchEnginePlugin(connector), "WebSearch")

    print("---------------- Question 1 -----------------\n")

    query = "Which country receives the most rain per year?"
    search = web_plugin["search"]
    result = await kernel.invoke(search, query=query)
    print(f"Question: {query}\n")
    print(f"Answer: {result}\n")

    print("---------------- Question 2 -----------------\n")

    prompt = """
    Answer the question using only the data that is provided in the data section.
    Do not use any prior knowledge to answer the question.
    Data: {{WebSearch.search "What is semantic kernel?"}}
    Question: {{$question}}?
    Answer:
    """

    req_settings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id
    )
    req_settings.temperature = 0.2

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        name="qna",
        template_format="semantic-kernel",
        execution_settings=req_settings,
    )

    question = "What is Semantic Kernel?"
    qna = kernel.add_function(
        function_name="qna",
        plugin_name="WebSearch",
        prompt_template_config=prompt_template_config,
    )
    result = await qna.invoke(kernel, question=question, num_results=10, offset=0)

    print(f"Question: {question}\n")
    print(f"Answer: {result}\n")

    """
    Output:
    Semantic Kernel is an open-source SDK that lets you easily combine AI services like OpenAI,
    Azure OpenAI, and Hugging Face with conventional programming languages like C# and Python.
    By doing so, you can create AI apps that combine the best of both worlds.
    Semantic Kernel is at the center of the copilot stack.
    """


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
