# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Any, Dict, Tuple

from openai import AsyncOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_assistant_settings import (
    OpenAIAssistantSettings,
)
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_function_call,
    get_function_calling_object,
)
from semantic_kernel.connectors.search_engine import BingConnector
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase

# Update the cwd to be the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


class WebSearchEngineSkill:
    """
    A search engine skill.
    """

    from semantic_kernel.orchestration.sk_context import SKContext
    from semantic_kernel.skill_definition import (
        sk_function,
        sk_function_context_parameter,
    )

    def __init__(self, connector) -> None:
        self._connector = connector

    @sk_function(
        description="Performs a web search for a given query", name="searchAsync"
    )
    @sk_function_context_parameter(
        name="query",
        description="The search query",
    )
    async def search_async(self, query: str, context: SKContext) -> str:
        query = query or context.variables.get("query")
        result = await self._connector.search_async(query, num_results=5, offset=0)
        if isinstance(result, list):
            result = " ".join(result)
        return str(result)


async def create_assistant(client) -> sk_oai.OpenAIChatCompletion:
    assistant = sk_oai.OpenAIChatCompletion(
        ai_model_id="gpt-3.5-turbo-1106",
        async_client=client,
        is_assistant=True,
    )

    file_path = os.path.join(script_dir, "assistants/tool_assistant.yaml")

    settings = OpenAIAssistantSettings.load_from_definition_file(file_path)

    await assistant.create_assistant_async(settings)
    return assistant


async def chat(
    context: sk.SKContext,
    kernel: sk.Kernel,
    functions: Dict[str, Any],
    chat_func: SKFunctionBase,
) -> Tuple[bool, sk.SKContext]:
    context = await chat_completion_with_function_call(
        kernel,
        chat_skill_name="ChatBot",
        chat_function_name="Chat",
        context=context,
        functions=functions,
        chat_function=chat_func,
    )
    print(f"Assistant:> {context.result}")


async def main() -> None:
    kernel = sk.Kernel()

    api_key, _ = sk.openai_settings_from_dot_env()

    client = AsyncOpenAI(api_key=api_key)
    assistant = await create_assistant(client)

    kernel = sk.Kernel()
    kernel.add_chat_service("oai_assistant", assistant)

    BING_API_KEY = sk.bing_search_settings_from_dot_env()
    connector = BingConnector(BING_API_KEY)
    kernel.import_skill(WebSearchEngineSkill(connector), skill_name="WebSearch")

    # enabling or disabling function calling is done by setting the function_call parameter for the completion.
    # when the function_call parameter is set to "auto" the model will decide which function to use, if any.
    # if you only want to use a specific function, set the name of that function in this parameter,
    # the format for that is 'SkillName-FunctionName', (i.e. 'math-Add').
    # if the model or api version do not support this you will get an error.
    prompt_config = sk.PromptTemplateConfig.from_completion_parameters(
        max_tokens=2000,
        temperature=0.7,
        top_p=0.8,
        function_call="auto",
    )
    prompt_template = OpenAIChatPromptTemplate(
        "{{$user_input}}", kernel.prompt_template_engine, prompt_config
    )

    function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
    chat_function = kernel.register_semantic_function(
        "ChatBot", "Chat", function_config
    )

    # calling the chat, you could add a overloaded version of the settings here,
    # to enable or disable function calling or set the function calling to a specific skill.
    # see the openai_function_calling example for how to use this with a unrelated function definition
    filter = {"exclude_skill": ["ChatBot"]}
    functions = get_function_calling_object(kernel, filter)

    context = kernel.create_new_context()
    context.variables[
        "user_input"
    ] = "I want to find a hotel in Seattle with free wifi and a pool."
    try:
        await chat(context, kernel, functions, chat_function)
    finally:
        # clean up resources
        await assistant.delete_thread_async()
        await assistant.delete_assistant_async()


if __name__ == "__main__":
    asyncio.run(main())
