# Copyright (c) Microsoft. All rights reserved.

import asyncio
from openai import AsyncOpenAI
import os
from typing import Any, Dict, Tuple

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import (
    OpenAIChatPromptTemplate,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_assistant_settings import (
    OpenAIAssistantSettings,
)
from semantic_kernel.connectors.ai.open_ai.utils import (
    chat_completion_with_function_call,
    get_function_calling_object,
)
from semantic_kernel.core_skills import MathSkill


# Update the cwd to be the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


async def create_assistant(client, api_key) -> sk_oai.OpenAIChatCompletion:
    assistant = sk_oai.OpenAIChatCompletion(
        ai_model_id="gpt-3.5-turbo-1106",
        api_key=api_key,
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
    print(f"Mosscap:> {context.result}")
    return True, context


async def main() -> None:

    kernel = sk.Kernel()

    api_key, _ = sk.openai_settings_from_dot_env()

    client = AsyncOpenAI(api_key=api_key)
    assistant = await create_assistant(client, api_key)

    kernel = sk.Kernel()
    kernel.add_chat_service("oai_assistant", assistant)

    skills_directory = os.path.join(__file__, "../../../../samples/skills")
    # adding skills to the kernel
    # the joke skill in the FunSkills is a semantic skill and has the function calling disabled.
    kernel.import_semantic_skill_from_directory(skills_directory, "FunSkill")
    # the math skill is a core skill and has the function calling enabled.
    kernel.import_skill(MathSkill(), skill_name="math")

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
    chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)

    # calling the chat, you could add a overloaded version of the settings here,
    # to enable or disable function calling or set the function calling to a specific skill.
    # see the openai_function_calling example for how to use this with a unrelated function definition
    filter = {"exclude_skill": ["ChatBot"]}
    functions = get_function_calling_object(kernel, filter)

    chatting = True
    context = kernel.create_new_context()
    context.variables[
        "user_input"
    ] = "I want to find a hotel in Seattle with free wifi and a pool."
    while chatting:
        chatting, context = await chat(context, kernel, functions, chat_function)


if __name__ == "__main__":
    asyncio.run(main())
